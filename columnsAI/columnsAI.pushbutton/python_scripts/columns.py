# pyRevit script.py - Sync Structural Columns from CSV (Robust Version)
# CSV assumptions:
# - column_id is unique key (stored in Mark parameter)
# - column_type = Revit Family name (e.g. "RC sq")
# - size = Revit Type name inside that family (e.g. "500mm")
# - base_level / top_level match Revit Level names exactly
# - alpha_grid / numeric_grid match Revit Grid names exactly

from pyrevit import revit, DB, forms
import csv
import sys

doc = revit.doc

DELETE_MISSING = False   # set True to delete columns not in CSV

# ----------------- helpers -----------------
def collect_levels():
    """Collect all levels in the project"""
    levels = {}
    try:
        collector = DB.FilteredElementCollector(doc).OfClass(DB.Level)
        for l in collector:
            if l and hasattr(l, 'Name'):
                levels[l.Name.strip()] = l
    except Exception as e:
        forms.alert("Error collecting levels: {}".format(str(e)))
    return levels

def collect_grids():
    """Collect all grids in the project"""
    grids = {}
    try:
        collector = DB.FilteredElementCollector(doc).OfClass(DB.Grid)
        for g in collector:
            if g and hasattr(g, 'Name'):
                grids[g.Name.strip()] = g
    except Exception as e:
        forms.alert("Error collecting grids: {}".format(str(e)))
    return grids

def grid_intersection_point(g1, g2):
    """
    Intersect two grid curves and return XYZ point.
    Uses line-line intersection in XY plane (works for any grid orientation).
    """
    try:
        curve1 = g1.Curve
        curve2 = g2.Curve

        if not curve1 or not curve2:
            return None

        # Get start and end points of each curve
        p1_start = curve1.GetEndPoint(0)
        p1_end = curve1.GetEndPoint(1)
        p2_start = curve2.GetEndPoint(0)
        p2_end = curve2.GetEndPoint(1)

        # Calculate intersection using 2D line-line math (ignore Z)
        x1, y1 = p1_start.X, p1_start.Y
        x2, y2 = p1_end.X, p1_end.Y
        x3, y3 = p2_start.X, p2_start.Y
        x4, y4 = p2_end.X, p2_end.Y

        denom = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
        if abs(denom) < 1e-10:  # parallel lines
            return None

        t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denom

        ix = x1 + t*(x2-x1)
        iy = y1 + t*(y2-y1)

        # Return point at Z=0 (base level elevation will be set separately)
        return DB.XYZ(ix, iy, 0)

    except Exception:
        return None

def existing_columns_by_mark():
    """Get all existing structural columns indexed by their Mark parameter"""
    out = {}
    try:
        cols = (DB.FilteredElementCollector(doc)
                .OfCategory(DB.BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType())

        for c in cols:
            try:
                # Use built-in Mark parameter (ALL_MODEL_MARK)
                p = c.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                if p and p.HasValue:
                    mark = p.AsString()
                    if mark:
                        out[mark] = c
            except:
                continue
    except Exception as e:
        forms.alert("Error collecting existing columns: {}".format(str(e)))

    return out

def get_all_column_types():
    """Get a dict of all available column family types: {(family_lower, type_lower): symbol}"""
    result = {}
    try:
        symbols = (DB.FilteredElementCollector(doc)
                   .OfCategory(DB.BuiltInCategory.OST_StructuralColumns)
                   .WhereElementIsElementType()
                   .ToElements())

        for s in symbols:
            try:
                # Get family name via SYMBOL_FAMILY_NAME_PARAM
                fam_param = s.get_Parameter(DB.BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)
                if not fam_param:
                    continue
                fam = (fam_param.AsString() or "").strip().lower()

                # Get type name via SYMBOL_NAME_PARAM or ALL_MODEL_TYPE_NAME
                type_param = s.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
                if not type_param:
                    type_param = s.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
                if not type_param:
                    continue
                name = (type_param.AsString() or "").strip().lower()

                if fam and name:
                    result[(fam, name)] = s

            except Exception:
                continue

    except Exception:
        pass

    return result

def find_symbol_strict(family_name, type_name, type_cache=None):
    """
    Find a FamilySymbol by exact family and type name match.
    Family name example: "RC sq"
    Type name example: "500mm"
    """
    fam_key = (family_name or "").strip().lower()
    type_key = (type_name or "").strip().lower()

    if not fam_key or not type_key:
        return None

    if type_cache:
        return type_cache.get((fam_key, type_key))

    return None

def set_base_top_levels(inst, base_level, top_level):
    """Set base and top levels for a column instance"""
    try:
        # Try to set base level
        p_base = inst.get_Parameter(DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
        if p_base and not p_base.IsReadOnly:
            p_base.Set(base_level.Id)

        # Try to set top level
        p_top = inst.get_Parameter(DB.BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
        if p_top and not p_top.IsReadOnly:
            p_top.Set(top_level.Id)

        return True
    except Exception as e:
        # Return False but don't crash
        return False

# ----------------- main -----------------
try:
    csv_path = forms.pick_file(file_ext="csv", title="Select columns CSV")
    if not csv_path:
        forms.alert("No CSV selected.", exitscript=True)

    # Read CSV
    with open(csv_path, "r") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        forms.alert("CSV file is empty!", exitscript=True)

    # Collect project data
    levels = collect_levels()
    grids = collect_grids()
    existing = existing_columns_by_mark()
    type_cache = get_all_column_types()
    csv_ids = set()

    # Check if we have necessary data
    if not levels:
        forms.alert("No levels found in project!", exitscript=True)
    if not grids:
        forms.alert("No grids found in project!", exitscript=True)
    if not type_cache:
        forms.alert("No structural column types found in project!\n\nAvailable types: {}".format(len(type_cache)), exitscript=True)

    # Statistics
    created = updated = skipped = deleted = 0
    skip_reasons = {}
    errors = []

    def skip(reason, detail=""):
        global skipped
        skipped += 1
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        if detail:
            errors.append("{}: {}".format(reason, detail))

    # Start transaction
    with revit.Transaction("Sync Columns From CSV"):
        for idx, r in enumerate(rows):
            try:
                cid = (r.get("column_id") or "").strip()
                if not cid:
                    skip("missing column_id", "row {}".format(idx + 2))
                    continue

                csv_ids.add(cid)

                # Get CSV values
                base_name = (r.get("base_level") or "").strip()
                top_name = (r.get("top_level") or "").strip()
                gA_name = (r.get("alpha_grid") or "").strip()
                gN_name = str(r.get("numeric_grid") or "").strip()
                fam_name = (r.get("column_type") or "").strip()
                type_name = (r.get("size") or "").strip()

                # Validate levels
                base_level = levels.get(base_name)
                top_level = levels.get(top_name)
                if not base_level or not top_level:
                    skip("level not found", "{}".format(cid))
                    continue

                # Validate grids
                gA = grids.get(gA_name)
                gN = grids.get(gN_name)
                if not gA or not gN:
                    skip("grid not found", "{}".format(cid))
                    continue

                # Get intersection point
                pt = grid_intersection_point(gA, gN)
                if not pt:
                    skip("grid intersection failed", "{}".format(cid))
                    continue

                # Find family symbol
                sym = find_symbol_strict(fam_name, type_name, type_cache)
                if not sym:
                    skip("family/type not found", "{} - {}".format(fam_name, type_name))
                    continue

                # Activate symbol if needed
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()

                # Check if column exists by Mark
                inst = existing.get(cid)

                if inst is None:
                    # CREATE NEW COLUMN
                    try:
                        inst = doc.Create.NewFamilyInstance(
                            pt, sym, base_level, DB.Structure.StructuralType.Column
                        )

                        if inst:
                            # Set Mark parameter to column_id
                            p_mark = inst.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                            if p_mark and not p_mark.IsReadOnly:
                                p_mark.Set(cid)

                            # Set levels
                            set_base_top_levels(inst, base_level, top_level)

                            created += 1
                        else:
                            skip("failed to create", "{}".format(cid))

                    except Exception as e:
                        skip("creation error", "{}: {}".format(cid, str(e)))

                else:
                    # UPDATE EXISTING COLUMN
                    try:
                        # Update location
                        loc = inst.Location
                        if isinstance(loc, DB.LocationPoint):
                            loc.Point = pt

                        # Update type if different
                        if inst.Symbol.Id != sym.Id:
                            inst.Symbol = sym

                        # Update levels
                        set_base_top_levels(inst, base_level, top_level)

                        updated += 1

                    except Exception as e:
                        skip("update error", "{}: {}".format(cid, str(e)))

            except Exception as e:
                skip("row processing error", "row {}: {}".format(idx + 2, str(e)))

        # Delete columns not in CSV (only if enabled)
        if DELETE_MISSING:
            try:
                for cid, inst in existing.items():
                    if cid not in csv_ids:
                        try:
                            doc.Delete(inst.Id)
                            deleted += 1
                        except:
                            pass
            except Exception as e:
                errors.append("Delete error: {}".format(str(e)))

    # ----------------- report -----------------
    msg_lines = [
        "CSV Sync Complete",
        "=" * 50,
        "",
        "Rows read  : {}".format(len(rows)),
        "Created    : {}".format(created),
        "Updated    : {}".format(updated),
        "Deleted    : {}".format(deleted),
        "Skipped    : {}".format(skipped),
    ]

    if skipped and skip_reasons:
        msg_lines.append("")
        msg_lines.append("Skip reasons:")
        for k in sorted(skip_reasons.keys()):
            msg_lines.append("  - {}: {}".format(k, skip_reasons[k]))

    if errors and len(errors) <= 10:
        msg_lines.append("")
        msg_lines.append("Recent errors:")
        for e in errors[-10:]:
            msg_lines.append("  - {}".format(e))

    # Show available types if family/type not found was an issue
    if "family/type not found" in skip_reasons:
        msg_lines.append("")
        msg_lines.append("Available column types ({} found):".format(len(type_cache)))
        for (fam, typ) in sorted(list(type_cache.keys())[:10]):
            msg_lines.append("  - '{}' : '{}'".format(fam, typ))
        if len(type_cache) > 10:
            msg_lines.append("  ... and {} more".format(len(type_cache) - 10))

    msg_lines.append("")
    msg_lines.append("Columns use 'Mark' parameter for tracking (column_id)")

    forms.alert("\n".join(msg_lines), title="Sync Complete")

except Exception as e:
    forms.alert("CRITICAL ERROR: {}\n\nType: {}".format(str(e), type(e).__name__),
                title="Script Failed")
    import traceback
    print(traceback.format_exc())
