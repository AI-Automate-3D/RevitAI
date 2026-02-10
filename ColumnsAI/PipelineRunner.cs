using System;
using System.Diagnostics;
using System.IO;

namespace ColumnsAI
{
    /// <summary>
    /// Finds a CPython 3.9+ installation with pandas and runs the AI pipeline.
    /// Same Python-detection logic as the original pyRevit script.
    /// </summary>
    public class PipelineRunner
    {
        private readonly string _workingDir;
        private readonly string _pipelineScript;

        public PipelineRunner(string workingDir)
        {
            _workingDir = workingDir;
            _pipelineScript = Path.Combine(workingDir, "run_pipeline.py");
        }

        public bool Run(out string error)
        {
            error = null;

            if (!File.Exists(_pipelineScript))
            {
                error = "Pipeline script not found: " + _pipelineScript;
                return false;
            }

            string pythonExe = FindPython();
            if (pythonExe == null)
            {
                error = "Could not find Python installation with pandas.\n\n" +
                        "Please install Python 3.9+ from python.org\n" +
                        "and install packages:  pip install pandas openai";
                return false;
            }

            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = pythonExe,
                    Arguments = "\"" + _pipelineScript + "\"",
                    WorkingDirectory = _workingDir,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using (var process = Process.Start(psi))
                {
                    string stdout = process.StandardOutput.ReadToEnd();
                    string stderr = process.StandardError.ReadToEnd();
                    process.WaitForExit();

                    // Write debug log
                    try
                    {
                        string logPath = Path.Combine(_workingDir, "debug_pipeline.log");
                        File.WriteAllText(logPath,
                            "=== Pipeline Execution Debug Log ===\r\n" +
                            "Python: " + pythonExe + "\r\n" +
                            "Return code: " + process.ExitCode + "\r\n\r\n" +
                            "=== STDOUT ===\r\n" + stdout + "\r\n\r\n" +
                            "=== STDERR ===\r\n" + stderr);
                    }
                    catch
                    {
                        // Log failure is non-critical
                    }

                    if (process.ExitCode != 0)
                    {
                        error = "Pipeline failed (exit code " + process.ExitCode + ")\n\n";
                        if (!string.IsNullOrEmpty(stderr))
                            error += "Errors:\n" + stderr;
                        else if (!string.IsNullOrEmpty(stdout))
                            error += "Output:\n" + stdout;
                        return false;
                    }
                }

                return true;
            }
            catch (Exception ex)
            {
                error = "Failed to execute pipeline:\n" + ex.Message;
                return false;
            }
        }

        private string FindPython()
        {
            string username = Environment.GetEnvironmentVariable("USERNAME") ?? "";

            string[] candidates = new string[]
            {
                Path.Combine(@"C:\Users", username, @"AppData\Local\Programs\Python\Python313\python.exe"),
                Path.Combine(@"C:\Users", username, @"AppData\Local\Programs\Python\Python312\python.exe"),
                Path.Combine(@"C:\Users", username, @"AppData\Local\Programs\Python\Python311\python.exe"),
                Path.Combine(@"C:\Users", username, @"AppData\Local\Programs\Python\Python310\python.exe"),
                Path.Combine(@"C:\Users", username, @"AppData\Local\Programs\Python\Python39\python.exe"),
                @"C:\Python313\python.exe",
                @"C:\Python312\python.exe",
                @"C:\Python311\python.exe",
                @"C:\Python310\python.exe",
                @"C:\Python39\python.exe",
                "python",
                "python3",
            };

            foreach (string candidate in candidates)
            {
                try
                {
                    if (candidate.Contains(@":\") && !File.Exists(candidate))
                        continue;

                    var psi = new ProcessStartInfo
                    {
                        FileName = candidate,
                        Arguments = "-c \"import pandas\"",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true
                    };

                    using (var process = Process.Start(psi))
                    {
                        process.WaitForExit(10000);
                        if (process.ExitCode == 0)
                            return candidate;
                    }
                }
                catch
                {
                    continue;
                }
            }

            return null;
        }
    }
}
