using System.Windows;
using System.Windows.Controls;

namespace ColumnsAI
{
    /// <summary>
    /// WPF dialog for natural language input. Same layout as the original pyRevit version:
    /// 700x400 window with a large text area and OK button.
    /// </summary>
    public class InputDialog : Window
    {
        private TextBox _textBox;

        public string UserInput { get; private set; }

        public InputDialog()
        {
            Title = "ColumnsAI - Natural Language Input";
            Width = 700;
            Height = 400;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            ResizeMode = ResizeMode.CanResize;

            var panel = new StackPanel();
            panel.Margin = new Thickness(20);

            var label = new Label();
            label.Content = "Enter your column modification request:";
            label.FontSize = 14;
            label.Margin = new Thickness(0, 0, 0, 10);
            panel.Children.Add(label);

            _textBox = new TextBox();
            _textBox.Height = 250;
            _textBox.TextWrapping = TextWrapping.Wrap;
            _textBox.AcceptsReturn = true;
            _textBox.VerticalScrollBarVisibility = ScrollBarVisibility.Auto;
            _textBox.FontSize = 12;
            _textBox.Margin = new Thickness(0, 0, 0, 20);
            panel.Children.Add(_textBox);

            var okBtn = new Button();
            okBtn.Content = "OK";
            okBtn.Height = 35;
            okBtn.FontSize = 14;
            okBtn.Click += OkBtn_Click;
            panel.Children.Add(okBtn);

            Content = panel;
        }

        private void OkBtn_Click(object sender, RoutedEventArgs e)
        {
            UserInput = _textBox.Text;
            DialogResult = true;
            Close();
        }
    }
}
