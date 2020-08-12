import pandas as pd

# https://www.istat.it/it/archivio/240401
# "Dataset con i decessi giornalieri" : https://www.istat.it/it/files//2020/03/Dataset-decessi-comunali-giornalieri-e-tracciato-record_al30giugno.zip

df = pd.read_csv("comuni_giornaliero_30giugno.csv", encoding="cp1252")

# Keep only Varese province
df = df[df.NOME_PROVINCIA == "Varese"]

# Keep only cities with 2020 data
df = df[df.TIPO_COMUNE == 1]

# Keep only total deaths
df = df[["GE", "T_15", "T_16", "T_17", "T_18", "T_19", "T_20"]]

# Replace n.d. with NaNs and sum daily totals
df["T_20"] = df["T_20"].replace("n.d.", float("nan"))
df["T_20"] = df["T_20"].astype(float)
# min_count=1 to keep NaNs instead of 0s https://github.com/pandas-dev/pandas/issues/20824
df = df.groupby(["GE"]).sum(min_count=1).reset_index()
df.columns = ["day", "2015", "2016", "2017", "2018", "2019", "2020"]
print(df)

# Unpivot yearly totals in different rows
df = pd.melt(
    df,
    id_vars=["day"],
    value_vars=["2015", "2016", "2017", "2018", "2019", "2020"],
    var_name="year",
    value_name="obituaries",
)

# Split day from month
days = df["day"].astype(str).str.extract(r"^(?P<month>\d{1,2})(?P<day>\d{2})$")

# Merge back month-day
df["day"] = days.month.str.rjust(2, "0") + "-" + days.day

df = df[["year", "day", "obituaries"]]

df = df.sort_values(["day", "year"])


df.to_csv("decessi_varese.csv", na_rep="null", float_format="%.0f", index=False)
