using System;
using System.IO;
using System.Reflection;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace ColumnsAI
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ColumnsAICommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                string addinDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
                string userInputFile = Path.Combine(addinDir, "user_input.txt");
                string inputHistoryDir = Path.Combine(addinDir, "input_history");
                string columnsCSV = Path.Combine(addinDir, "columns.csv");

                // Ensure directories exist
                if (!Directory.Exists(inputHistoryDir))
                    Directory.CreateDirectory(inputHistoryDir);

                // Show input dialog
                var dialog = new InputDialog();
                bool? result = dialog.ShowDialog();

                if (result != true || string.IsNullOrWhiteSpace(dialog.UserInput))
                    return Result.Cancelled;

                string userInput = dialog.UserInput.Trim();

                // Confirm with user
                TaskDialog confirmDlg = new TaskDialog("Confirm Input");
                confirmDlg.MainContent = "You entered:\n\n\"" + userInput + "\"\n\nProceed with processing?";
                confirmDlg.CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No;
                confirmDlg.DefaultButton = TaskDialogResult.Yes;

                if (confirmDlg.Show() != TaskDialogResult.Yes)
                    return Result.Cancelled;

                // Save user input to file
                File.WriteAllText(userInputFile, userInput);

                // Run AI pipeline with external Python
                var runner = new PipelineRunner(addinDir);
                string pipelineError;
                if (!runner.Run(out pipelineError))
                {
                    TaskDialog.Show("Pipeline Error",
                        "Pipeline execution failed.\n\n" + pipelineError);
                    return Result.Failed;
                }

                // Archive the input
                ArchiveInput(userInput, inputHistoryDir);

                // Clear user_input.txt
                File.WriteAllText(userInputFile, "");

                // Sync modified CSV with Revit
                Document doc = commandData.Application.ActiveUIDocument.Document;
                var syncer = new ColumnSyncer(doc);
                string syncReport = syncer.SyncFromCSV(columnsCSV);

                // Show result
                TaskDialog.Show("ColumnsAI Complete", syncReport);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("ColumnsAI Error",
                    "Critical error:\n\n" + ex.Message + "\n\nType: " + ex.GetType().Name);
                return Result.Failed;
            }
        }

        private void ArchiveInput(string content, string historyDir)
        {
            try
            {
                string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string archivePath = Path.Combine(historyDir, "input_" + timestamp + ".txt");
                File.WriteAllText(archivePath, content);
            }
            catch
            {
                // Archival failure is non-critical
            }
        }
    }
}
