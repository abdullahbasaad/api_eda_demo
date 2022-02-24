
import pandas as pd 

class Data_wrangling:

    def __init__(self, df):
        self.df = df

    def check_categorical_variables(self):
        data = {}
        categories_col = []
        for col in list(self.df.columns):
            if ((self.df[col].size - len(self.df[col].dropna().unique())) / self.df[col].size * 100 > 91):
                categories_col.append(col)
        
        if len(categories_col) > 0:
            for col in categories_col:
                if (self.df[col].dtypes) == object:
                    data[col] = pd.get_dummies(self.df[col], drop_first = True)

        for i, v in data.items():
            self.df[i] = v
        return self.df, categories_col

    def return_columns_has_missing_values(self):
        col_has_missing = []
        if self.df.isna().sum().any():
            for col in list(self.df.columns):
                if self.df[col].isna().sum() > 0:
                    col_has_missing.append(col)
        return col_has_missing

    def exclude_features_with_high_missing_values(self): # Has missing more the half of total values
        if self.df.isna().sum().any():
            ds_rows = self.df.shape[0] 
            for col in list(self.df.columns):
                if self.df[col].isnull().sum() > ds_rows/2:
                    self.df = self.df.drop(col, 1)
            return self.df

    def selected_features_correlation(df):
        pass



    
