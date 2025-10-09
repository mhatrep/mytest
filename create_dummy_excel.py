import pandas as pd

# Create some sample data
data1 = {'col1': [1, 2], 'col2': [3, 4]}
df1 = pd.DataFrame(data=data1)

data2 = {'colA': ['A', 'B'], 'colB': ['C', 'D']}
df2 = pd.DataFrame(data=data2)

# Create a Pandas Excel writer using openpyxl as the engine
with pd.ExcelWriter('test.xlsx', engine='openpyxl') as writer:
    df1.to_excel(writer, sheet_name='Sheet1', index=False)
    df2.to_excel(writer, sheet_name='Sheet2', index=False)

print("Dummy Excel file 'test.xlsx' created successfully.")