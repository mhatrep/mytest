import unittest
import wx
import os
import time
from sql_visualizer import MainFrame

class TestSQLVisualizer(unittest.TestCase):
    def setUp(self):
        self.app = wx.App(False)
        self.frame = MainFrame()
        self.frame.Show()

    def tearDown(self):
        # Allow events to process before closing
        wx.Yield()
        if self.frame:
             self.frame.Close(True)
        if self.app:
            self.app.Destroy()
        if os.path.exists('sql_graph.png'):
            os.remove('sql_graph.png')
        if os.path.exists('sql_graph'):
            os.remove('sql_graph')


    def test_visualization_flow(self):
        # This function contains the core test logic
        def test_logic():
            try:
                # 1. Set SQL query
                test_sql = "SELECT c.name, p.product_name FROM customers c JOIN purchases p ON c.id = p.customer_id WHERE p.price > 100"
                self.frame.sql_input.SetValue(test_sql)

                # 2. Simulate button click
                visualize_button = [child for child in self.frame.panel.GetChildren() if isinstance(child, wx.Button)][0]
                click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, visualize_button.GetId())
                wx.PostEvent(visualize_button.GetEventHandler(), click_event)

                # 3. Wait for graph generation
                wx.Yield()
                time.sleep(2) # Give time for file I/O and UI update

                # 4. Assert that the graph image was created
                self.assertTrue(os.path.exists('sql_graph.png'), "Graph image file was not created.")

                # 5. Assert that the image is displayed in the panel
                bitmap = self.frame.image_panel.GetBitmap()
                self.assertIsNotNone(bitmap, "Bitmap should not be None.")
                self.assertTrue(bitmap.IsOk(), "Bitmap should be valid.")
                self.assertGreater(bitmap.GetWidth(), 1, "Bitmap width should be > 1.")
                self.assertGreater(bitmap.GetHeight(), 1, "Bitmap height should be > 1.")
            finally:
                # Ensure the app closes to terminate the test
                self.frame.Close()

        # Use CallAfter to run the test logic once the wx.App event loop has started
        wx.CallAfter(test_logic)
        self.app.MainLoop()

if __name__ == '__main__':
    # Run the test within a virtual framebuffer
    if "DISPLAY" in os.environ:
        unittest.main()
    else:
        print("Skipping test: DISPLAY environment variable not set. Run within a virtual framebuffer like Xvfb.")