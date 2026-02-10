using System;
using System.Reflection;
using Autodesk.Revit.UI;

namespace ColumnsAI
{
    public class App : IExternalApplication
    {
        public Result OnStartup(UIControlledApplication application)
        {
            try
            {
                string tabName = "ColumnsAI";
                application.CreateRibbonTab(tabName);

                RibbonPanel panel = application.CreateRibbonPanel(tabName, "Tools");

                string assemblyPath = Assembly.GetExecutingAssembly().Location;

                PushButtonData buttonData = new PushButtonData(
                    "cmdColumnsAI",
                    "Columns\nAI",
                    assemblyPath,
                    "ColumnsAI.ColumnsAICommand"
                );

                buttonData.ToolTip = "AI-powered structural column modifications using natural language";
                buttonData.LongDescription =
                    "Enter a natural language request to modify structural columns.\n" +
                    "The AI will parse your request and update columns in the model.";

                panel.AddItem(buttonData);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                TaskDialog.Show("ColumnsAI Error",
                    "Failed to initialize ColumnsAI:\n" + ex.Message);
                return Result.Failed;
            }
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            return Result.Succeeded;
        }
    }
}
