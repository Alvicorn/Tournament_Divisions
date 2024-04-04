from datetime import datetime
from functools import partial
import os
import tkinter as tk
from tkinter import filedialog

import pandas as pd


PRIMARY_HEADERS = [
    "Participant's Name: First",
    "Participant's Name: Last",
    "EMA Location Participant is From",
    "Height (in total inches)",
    "Weight (in total lbs)",
    "Belt Level",
    "Gender",  # from pre_proc()
]


DIVISION_HEADERS = {
    "Division Entering:: Forms": "Forms",
    "Division Entering:: Weapons": "Weapons",
    "Division Entering:: Grappling": "Grappling",
    "Division Entering:: Sparring": "Sparring",
}


EXTRA_DIVISION_HEADERS = {
    "Extra Divisions:: Team Forms - 12 Years and Under Only (Bonus Division) +$10": "Team Forms",
    "Extra Divisions:: Musical Weapons - All Ages (Bonus Division) +$10 (modified)": "Musical Weapons",
}


CUSTOM_DIVISION_HEADERS = {
    "Extra Divisions:: Team Forms - 12 Years and Under Only (Bonus Division) +$10": [
        "Teammates Names for Team Forms"
    ]
}


BELT_LEVELS = [
    "White",
    "White Belt Black Stripe",
    "Yellow",
    "Yellow Belt Black Stripe",
    "Orange",
    "Orange Belt Black Stripe",
    "Green",
    "Green Belt Black Stripe",
    "Blue",
    "Blue Belt Black Stripe",
    "Purple",
    "Purple Belt Black Stripe",
    "Red",
    "Red Belt Black Stripe",
    "Brown",
    "Brown Belt Blue Stripe",
    "Brown Belt Red Stripe",
    "Brown Belt Black Stripe",
    "Black",
]


BELT_DIVISIONS = [
    "White",
    "Yellow",
    "Orange",
    "Green",
    "Blue",
    "Purple",
    "Red",
    "Brown",
    "Black",
]


def output_directory_setup() -> str:
    out_dir = f"output_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}"
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    return out_dir


def export_df_as_xlsx(dir: str, df: pd.DataFrame, file_name: str) -> None:
    df.to_excel(f"{dir}/{file_name}.xlsx", index=False)


def export_df_as_xlsx_sheets(
    dir: str, dfs: dict[str : dict[str : pd.DataFrame]]
) -> None:
    for belt_level, data_dfs in dfs.items():
        with pd.ExcelWriter(f"{dir}/{belt_level}.xlsx") as writer:
            for division, df in data_dfs.items():
                df.to_excel(writer, sheet_name=division, index=False)


def duplicate_df_by_a_division(
    division_name: str, parent_df: pd.DataFrame
) -> pd.DataFrame:
    df = parent_df[parent_df[division_name].notna()]

    # remove unnessesary headers
    target_headers = (
        PRIMARY_HEADERS
        + [division_name]
        + CUSTOM_DIVISION_HEADERS.get(division_name, [])
    )

    return df[df.columns.intersection(target_headers)]


def pre_proc(df: pd.DataFrame) -> pd.DataFrame:
    # merge the gender columns into one
    df["Gender"] = df["Gender: Male"].fillna(df["Gender: Female"]).astype(str)
    df.drop(["Gender: Male", "Gender: Female"], axis=1, inplace=True)

    # sort the df
    # TODO: data is missing age
    #! Belt Level > Gender > Age > weight > height
    df["Belt Level"] = pd.Categorical(
        df["Belt Level"], categories=BELT_LEVELS, ordered=True
    )

    df["Gender"] = pd.Categorical(
        df["Gender"], categories=["Female", "Male"], ordered=True
    )

    df = df.sort_values(
        by=[
            "Belt Level",
            "Gender",
            "Weight (in total lbs)",
            "Height (in total inches)",
        ]
    )
    return df


def extract_to_divisions(filepath: str) -> str:
    df = pre_proc(pd.read_csv(filepath))

    # duplicate common data and split by divisions
    divisions = {
        division_name: duplicate_df_by_a_division(division_header, df)
        for division_header, division_name in {
            **DIVISION_HEADERS,
            **EXTRA_DIVISION_HEADERS,
        }.items()
    }

    out_dir = output_directory_setup()

    female_xlsx_sheets = {
        f"{belt_level}_Belt_Female": {} for belt_level in BELT_DIVISIONS
    }
    male_xlsx_sheets = {f"{belt_level}_Belt_Male": {} for belt_level in BELT_DIVISIONS}

    for division_name, competitors_df in divisions.items():
        # TODO: split extra divisions into sub_divisions
        if division_name in EXTRA_DIVISION_HEADERS.values():
            export_df_as_xlsx(out_dir, competitors_df, f"{division_name}")
        else:
            for belt_division in BELT_DIVISIONS:
                sub_division = competitors_df[
                    competitors_df["Belt Level"].str.startswith(belt_division)
                ]
                female_sub_division = sub_division[sub_division["Gender"] == "Female"]
                male_sub_division = sub_division[sub_division["Gender"] == "Male"]

                female_xlsx_sheets[f"{belt_division}_Belt_Female"][division_name] = (
                    female_sub_division
                )
                male_xlsx_sheets[f"{belt_division}_Belt_Male"][division_name] = (
                    male_sub_division
                )

    export_df_as_xlsx_sheets(out_dir, female_xlsx_sheets)
    export_df_as_xlsx_sheets(out_dir, male_xlsx_sheets)
    return os.path.abspath(out_dir)


def open_file_dialog(label: tk.Label) -> None:
    filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filepath:
        out_dir = extract_to_divisions(filepath)
        label.config(text=f"Folder Path: {out_dir}")


def main():
    # Create a tkinter window
    root = tk.Tk()
    root.title("EMA Tournament Division Generator")

    # Create a button to open the file dialog
    label = tk.Label(root, text="")
    label.pack(padx=10, pady=10)

    button = tk.Button(
        root, text="Open CSV File", command=partial(open_file_dialog, label)
    )
    button.pack(pady=10)
    root.mainloop()


if __name__ == "__main__":
    main()
