import wx
import sqlglot
from sqlglot import exp
import graphviz
import os

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="SQL Visualizer", size=(800, 600))

        self.panel = wx.Panel(self)

        # Create a sizer for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # SQL input text control
        self.sql_input = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
        main_sizer.Add(self.sql_input, 1, wx.EXPAND | wx.ALL, 5)

        # Visualize button
        visualize_button = wx.Button(self.panel, label="Visualize")
        visualize_button.Bind(wx.EVT_BUTTON, self.on_visualize)
        main_sizer.Add(visualize_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # Image display panel
        self.image_panel = wx.StaticBitmap(self.panel)
        main_sizer.Add(self.image_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.panel.SetSizer(main_sizer)
        self.Show()

    def on_visualize(self, event):
        sql = self.sql_input.GetValue()
        if not sql:
            print("Error: Please enter a SQL query.")
            return

        try:
            # Clear previous image
            self.image_panel.SetBitmap(wx.Bitmap(1,1))

            parsed = sqlglot.parse_one(sql)
            dot = graphviz.Digraph('sql-graph', comment='SQL Query Structure')
            dot.attr('node', shape='box', style='rounded')

            from_clause = parsed.find(exp.From)
            if not from_clause:
                print("Info: SQL query has no FROM clause to visualize.")
                return

            # Add tables as nodes
            tables = {table.name for table in parsed.find_all(exp.Table)}
            for table in tables:
                dot.node(table, table)

            # Add joins as edges
            source_table = from_clause.this.name
            for join in parsed.find_all(exp.Join):
                target_table = join.this.name
                join_type = join.args.get('kind', 'INNER')
                join_condition = str(join.on)
                dot.edge(source_table, target_table, label=f'{join_type} JOIN\n({join_condition})')
                source_table = target_table # For subsequent joins

            # Add where clause
            where_clause = parsed.find(exp.Where)
            if where_clause:
                where_condition = str(where_clause.this)
                dot.node('filter', f'WHERE\n{where_condition}', shape='diamond')
                dot.edge(source_table, 'filter', style='dashed')

            # Render and display the graph
            graph_path = dot.render('sql_graph', format='png', cleanup=True, view=False)

            if os.path.exists(graph_path):
                image = wx.Image(graph_path, wx.BITMAP_TYPE_PNG)
                bitmap = wx.Bitmap(image)
                self.image_panel.SetBitmap(bitmap)
                self.panel.Layout()
                print("Graph generated and displayed successfully!")
            else:
                 print("Error: Could not generate graph image.")

        except Exception as e:
            print(f"Error generating graph: {e}")

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()