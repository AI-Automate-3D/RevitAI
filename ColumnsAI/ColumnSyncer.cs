using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Structure;

namespace ColumnsAI
{
    /// <summary>
    /// Syncs structural columns from a CSV file into the Revit model.
    /// Direct C# port of the original pyRevit columns.py script.
    /// </summary>
    public class ColumnSyncer
    {
        private readonly Document _doc;
        private const bool DELETE_MISSING = false;

        public ColumnSyncer(Document doc)
        {
            _doc = doc;
        }

        public string SyncFromCSV(string csvPath)
        {
            if (!File.Exists(csvPath))
                return "Error: Columns CSV not found: " + csvPath;

            // Read CSV
            var rows = ReadCSV(csvPath);
            if (rows.Count == 0)
                return "Error: CSV file is empty!";

            // Collect project data
            var levels = CollectLevels();
            var grids = CollectGrids();
            var existing = ExistingColumnsByMark();
            var typeCache = GetAllColumnTypes();
            var csvIds = new HashSet<string>();

            if (levels.Count == 0) return "Error: No levels found in project!";
            if (grids.Count == 0) return "Error: No grids found in project!";
            if (typeCache.Count == 0) return "Error: No structural column types found in project!";

            // Statistics
            int created = 0, updated = 0, skipped = 0, deleted = 0;
            var skipReasons = new Dictionary<string, int>();
            var errors = new List<string>();

            // Start transaction
            using (var trans = new Transaction(_doc, "Sync Columns From CSV"))
            {
                trans.Start();

                for (int idx = 0; idx < rows.Count; idx++)
                {
                    var r = rows[idx];
                    try
                    {
                        string cid = GetValue(r, "column_id");
                        if (string.IsNullOrEmpty(cid))
                        {
                            Skip(ref skipped, skipReasons, errors,
                                "missing column_id", "row " + (idx + 2));
                            continue;
                        }

                        csvIds.Add(cid);

                        string baseName = GetValue(r, "base_level");
                        string topName = GetValue(r, "top_level");
                        string alphaName = GetValue(r, "alpha_grid");
                        string numericName = GetValue(r, "numeric_grid");
                        string famName = GetValue(r, "column_type");
                        string typeName = GetValue(r, "size");

                        // Validate levels
                        Level baseLevel, topLevel;
                        if (!levels.TryGetValue(baseName, out baseLevel) ||
                            !levels.TryGetValue(topName, out topLevel))
                        {
                            Skip(ref skipped, skipReasons, errors,
                                "level not found", cid);
                            continue;
                        }

                        // Validate grids
                        Grid gridA, gridN;
                        if (!grids.TryGetValue(alphaName, out gridA) ||
                            !grids.TryGetValue(numericName, out gridN))
                        {
                            Skip(ref skipped, skipReasons, errors,
                                "grid not found", cid);
                            continue;
                        }

                        // Get intersection point
                        XYZ pt = GridIntersectionPoint(gridA, gridN);
                        if (pt == null)
                        {
                            Skip(ref skipped, skipReasons, errors,
                                "grid intersection failed", cid);
                            continue;
                        }

                        // Find family symbol
                        FamilySymbol sym = FindSymbolStrict(famName, typeName, typeCache);
                        if (sym == null)
                        {
                            Skip(ref skipped, skipReasons, errors,
                                "family/type not found", famName + " - " + typeName);
                            continue;
                        }

                        // Activate symbol if needed
                        if (!sym.IsActive)
                        {
                            sym.Activate();
                            _doc.Regenerate();
                        }

                        // Check if column exists by Mark
                        FamilyInstance inst;
                        if (!existing.TryGetValue(cid, out inst))
                        {
                            // CREATE NEW COLUMN
                            try
                            {
                                inst = _doc.Create.NewFamilyInstance(
                                    pt, sym, baseLevel, StructuralType.Column);

                                if (inst != null)
                                {
                                    var pMark = inst.get_Parameter(
                                        BuiltInParameter.ALL_MODEL_MARK);
                                    if (pMark != null && !pMark.IsReadOnly)
                                        pMark.Set(cid);

                                    SetBaseTopLevels(inst, baseLevel, topLevel);
                                    created++;
                                }
                                else
                                {
                                    Skip(ref skipped, skipReasons, errors,
                                        "failed to create", cid);
                                }
                            }
                            catch (Exception ex)
                            {
                                Skip(ref skipped, skipReasons, errors,
                                    "creation error", cid + ": " + ex.Message);
                            }
                        }
                        else
                        {
                            // UPDATE EXISTING COLUMN
                            try
                            {
                                var loc = inst.Location as LocationPoint;
                                if (loc != null)
                                    loc.Point = pt;

                                if (inst.Symbol.Id != sym.Id)
                                    inst.Symbol = sym;

                                SetBaseTopLevels(inst, baseLevel, topLevel);
                                updated++;
                            }
                            catch (Exception ex)
                            {
                                Skip(ref skipped, skipReasons, errors,
                                    "update error", cid + ": " + ex.Message);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Skip(ref skipped, skipReasons, errors,
                            "row processing error",
                            "row " + (idx + 2) + ": " + ex.Message);
                    }
                }

                // Delete columns not in CSV (only if enabled)
                if (DELETE_MISSING)
                {
                    foreach (var kvp in existing)
                    {
                        if (!csvIds.Contains(kvp.Key))
                        {
                            try
                            {
                                _doc.Delete(kvp.Value.Id);
                                deleted++;
                            }
                            catch
                            {
                                // Deletion failure is non-critical
                            }
                        }
                    }
                }

                trans.Commit();
            }

            return BuildReport(rows.Count, created, updated, deleted, skipped,
                               skipReasons, errors, typeCache);
        }

        // ----- Revit data collectors -----

        private Dictionary<string, Level> CollectLevels()
        {
            var levels = new Dictionary<string, Level>();
            var collector = new FilteredElementCollector(_doc).OfClass(typeof(Level));
            foreach (Level l in collector)
            {
                if (l != null && l.Name != null)
                    levels[l.Name.Trim()] = l;
            }
            return levels;
        }

        private Dictionary<string, Grid> CollectGrids()
        {
            var grids = new Dictionary<string, Grid>();
            var collector = new FilteredElementCollector(_doc).OfClass(typeof(Grid));
            foreach (Grid g in collector)
            {
                if (g != null && g.Name != null)
                    grids[g.Name.Trim()] = g;
            }
            return grids;
        }

        private Dictionary<string, FamilyInstance> ExistingColumnsByMark()
        {
            var result = new Dictionary<string, FamilyInstance>();
            var collector = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType();

            foreach (Element e in collector)
            {
                var fi = e as FamilyInstance;
                if (fi == null) continue;

                var p = fi.get_Parameter(BuiltInParameter.ALL_MODEL_MARK);
                if (p != null && p.HasValue)
                {
                    string mark = p.AsString();
                    if (!string.IsNullOrEmpty(mark))
                        result[mark] = fi;
                }
            }
            return result;
        }

        private Dictionary<string, FamilySymbol> GetAllColumnTypes()
        {
            var result = new Dictionary<string, FamilySymbol>();
            var collector = new FilteredElementCollector(_doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType();

            foreach (Element e in collector)
            {
                var sym = e as FamilySymbol;
                if (sym == null) continue;

                var famParam = sym.get_Parameter(
                    BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM);
                if (famParam == null) continue;
                string fam = (famParam.AsString() ?? "").Trim().ToLower();

                var typeParam = sym.get_Parameter(
                    BuiltInParameter.SYMBOL_NAME_PARAM);
                if (typeParam == null)
                    typeParam = sym.get_Parameter(
                        BuiltInParameter.ALL_MODEL_TYPE_NAME);
                if (typeParam == null) continue;
                string name = (typeParam.AsString() ?? "").Trim().ToLower();

                if (!string.IsNullOrEmpty(fam) && !string.IsNullOrEmpty(name))
                    result[fam + "|" + name] = sym;
            }
            return result;
        }

        // ----- Geometry helpers -----

        private XYZ GridIntersectionPoint(Grid g1, Grid g2)
        {
            try
            {
                Curve curve1 = g1.Curve;
                Curve curve2 = g2.Curve;
                if (curve1 == null || curve2 == null) return null;

                XYZ p1s = curve1.GetEndPoint(0);
                XYZ p1e = curve1.GetEndPoint(1);
                XYZ p2s = curve2.GetEndPoint(0);
                XYZ p2e = curve2.GetEndPoint(1);

                double x1 = p1s.X, y1 = p1s.Y;
                double x2 = p1e.X, y2 = p1e.Y;
                double x3 = p2s.X, y3 = p2s.Y;
                double x4 = p2e.X, y4 = p2e.Y;

                double denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
                if (Math.Abs(denom) < 1e-10) return null;

                double t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
                double ix = x1 + t * (x2 - x1);
                double iy = y1 + t * (y2 - y1);

                return new XYZ(ix, iy, 0);
            }
            catch
            {
                return null;
            }
        }

        private FamilySymbol FindSymbolStrict(string familyName, string typeName,
                                               Dictionary<string, FamilySymbol> cache)
        {
            string famKey = (familyName ?? "").Trim().ToLower();
            string typeKey = (typeName ?? "").Trim().ToLower();
            if (string.IsNullOrEmpty(famKey) || string.IsNullOrEmpty(typeKey))
                return null;

            FamilySymbol sym;
            cache.TryGetValue(famKey + "|" + typeKey, out sym);
            return sym;
        }

        private void SetBaseTopLevels(FamilyInstance inst, Level baseLevel, Level topLevel)
        {
            var pBase = inst.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
            if (pBase != null && !pBase.IsReadOnly)
                pBase.Set(baseLevel.Id);

            var pTop = inst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
            if (pTop != null && !pTop.IsReadOnly)
                pTop.Set(topLevel.Id);
        }

        // ----- CSV reader -----

        private List<Dictionary<string, string>> ReadCSV(string path)
        {
            var rows = new List<Dictionary<string, string>>();
            var lines = File.ReadAllLines(path);
            if (lines.Length < 2) return rows;

            string[] headers = lines[0].Split(',');
            for (int i = 0; i < headers.Length; i++)
                headers[i] = headers[i].Trim();

            for (int i = 1; i < lines.Length; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i])) continue;
                string[] values = lines[i].Split(',');
                var row = new Dictionary<string, string>();
                for (int j = 0; j < headers.Length && j < values.Length; j++)
                    row[headers[j]] = values[j].Trim();
                rows.Add(row);
            }
            return rows;
        }

        private string GetValue(Dictionary<string, string> row, string key)
        {
            string val;
            if (row.TryGetValue(key, out val))
                return val.Trim();
            return "";
        }

        // ----- Helpers -----

        private void Skip(ref int skipped, Dictionary<string, int> skipReasons,
                          List<string> errors, string reason, string detail)
        {
            skipped++;
            if (!skipReasons.ContainsKey(reason))
                skipReasons[reason] = 0;
            skipReasons[reason]++;
            if (!string.IsNullOrEmpty(detail))
                errors.Add(reason + ": " + detail);
        }

        private string BuildReport(int totalRows, int created, int updated,
                                    int deleted, int skipped,
                                    Dictionary<string, int> skipReasons,
                                    List<string> errors,
                                    Dictionary<string, FamilySymbol> typeCache)
        {
            var sb = new StringBuilder();
            sb.AppendLine("CSV Sync Complete");
            sb.AppendLine(new string('=', 50));
            sb.AppendLine();
            sb.AppendLine("Rows read  : " + totalRows);
            sb.AppendLine("Created    : " + created);
            sb.AppendLine("Updated    : " + updated);
            sb.AppendLine("Deleted    : " + deleted);
            sb.AppendLine("Skipped    : " + skipped);

            if (skipped > 0 && skipReasons.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine("Skip reasons:");
                foreach (var kvp in skipReasons.OrderBy(x => x.Key))
                    sb.AppendLine("  - " + kvp.Key + ": " + kvp.Value);
            }

            if (errors.Count > 0 && errors.Count <= 10)
            {
                sb.AppendLine();
                sb.AppendLine("Recent errors:");
                foreach (var e in errors.Skip(Math.Max(0, errors.Count - 10)))
                    sb.AppendLine("  - " + e);
            }

            if (skipReasons.ContainsKey("family/type not found"))
            {
                sb.AppendLine();
                sb.AppendLine("Available column types (" + typeCache.Count + " found):");
                int count = 0;
                foreach (var key in typeCache.Keys.OrderBy(x => x))
                {
                    if (count >= 10) break;
                    var parts = key.Split('|');
                    sb.AppendLine("  - '" + parts[0] + "' : '" +
                        (parts.Length > 1 ? parts[1] : "") + "'");
                    count++;
                }
                if (typeCache.Count > 10)
                    sb.AppendLine("  ... and " + (typeCache.Count - 10) + " more");
            }

            sb.AppendLine();
            sb.AppendLine("Columns use 'Mark' parameter for tracking (column_id)");
            return sb.ToString();
        }
    }
}
