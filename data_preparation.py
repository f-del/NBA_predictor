import pandas as pd

def transform_position_to_array(df, column_name):
    """Transforms a position column with string values into an array of positions."""
    df[column_name] = df[column_name].apply(lambda x: x.split(" and ") if isinstance(x, str) else x)
    return df

def split_weight_units(df, column_name):
    """Splits the weight column into separate values for pounds and kilograms, removing the original column."""
    def split_weight(weight):
        if isinstance(weight, str):
            parts = weight.split(" (")
            pounds = parts[0].replace("lb", "").strip()
            kg = parts[1].replace("kg)", "").strip() if len(parts) > 1 else None
            return {"pounds": pounds, "kilograms": kg}
        return {"pounds": None, "kilograms": None}

    weights = df[column_name].apply(split_weight)
    df["Weight (pounds)"] = weights.apply(lambda x: x["pounds"])
    df["Weight (kilograms)"] = weights.apply(lambda x: x["kilograms"])
    df.drop(columns=[column_name], inplace=True)
    return df


def convert_height_to_meters(df, column_name):
    """Converts height from feet-inches format to meters and adds a new column."""

    def convert_height(height):
        if isinstance(height, str):
            try:
                feet, inches = map(float, height.split("-"))
                meters = feet * 0.3048 + inches * 0.0254
                return round(meters, 2)
            except (ValueError, TypeError):
                return None
        return None

    df["Height (meters)"] = df[column_name].apply(convert_height)
    return df

def convert_dates_to_datetime(df, columns):
    """Converts date columns from text representation to Python datetime format."""
    for column in columns:
        df[column] = pd.to_datetime(df[column], format="%B %d, %Y")
    return df