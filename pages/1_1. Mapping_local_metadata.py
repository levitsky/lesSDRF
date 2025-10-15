import streamlit as st
import pandas as pd
import numpy as np
import re
import ParsingModule
import warnings
warnings.filterwarnings("ignore")
from PIL import Image
import base64
import io


st.set_page_config(
    page_title="Map local metadata",
    layout="wide",
    page_icon="🧪",
    menu_items={
        "Get help": "https://github.com/compomics/lesSDRF/issues",
        "Report a bug": "https://github.com/compomics/lesSDRF/issues",
    },
)

def add_logo(logo_path, width, height):
    """Read and return a resized logo"""
    logo = Image.open(logo_path)
    modified_logo = logo.resize((width, height))
    return modified_logo

def get_base64_image(image):
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    return img_str

my_logo = add_logo(logo_path="final_logo.png", width=149, height=58)

st.markdown(
    f"""
    <style>
        [data-testid="stSidebarNav"] {{
            background-image: url('data:image/png;base64,{get_base64_image(my_logo)}');
            background-repeat: no-repeat;
            background-position: 40px 20px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("1. Map local metadata to SDRF")
st.markdown(
    """If you have a local metadata file available, you can use this file to map the data to the required SDRF information. """
)
st.markdown(
    """**Important:** you can upload the file in csv, tsv or xlsx format.
The order of your raw file names should match the order in which you inputted them in the previous step"""
)




data_dict = st.session_state["data_dict"]

# if template_df is not in the session state, don't run all the code below
if "template_df" not in st.session_state:
    st.error("Please fill in the template file in the Home page first", icon="🚨")
    st.stop()
else:
    template_df = st.session_state["template_df"]
    st.write("**This is your current SDRF file.**")
    st.write(template_df)

with st.sidebar:
    download = st.download_button("Press to download SDRF file",ParsingModule.convert_df(template_df), "intermediate_SDRF.sdrf.tsv", help="download your SDRF file")
    st.write("""Please refer to your data and lesSDRF within your manuscript as follows:
                 *The experimental metadata has been generated using lesSDRF and is available through ProteomeXchange with the dataset identifier [PXDxxxxxxx]*""")
# Ask the user to upload their own metadata file and to map it to the columns of the template file
metadata_sheet = st.file_uploader(
    "Upload your local metadata file (.csv, .tsv or .xls)", type=["csv", "tsv", "xlsx"]
)
if metadata_sheet is not None:
    file_extension = metadata_sheet.name.split(".")[-1]
    if file_extension == "csv":
        metadata_df = pd.read_csv(metadata_sheet)
    elif file_extension == "tsv":
        metadata_df = pd.read_csv(metadata_sheet, sep="\t")
    elif file_extension == "xlsx":
        metadata_df = pd.read_excel(metadata_sheet)
    st.write("Your metadata file:")
    st.dataframe(metadata_df)
    if "metadata_df" not in st.session_state:
        st.session_state["metadata_df"] = metadata_df
    # Check for potential mismatch in number of samples
    if metadata_df.shape[0] != template_df.shape[0]:
        st.error(
            "There is a mismatch in the number of uploaded files and the number of files in the metadata sheet",
            icon="🚨",
        )


    meta_columns = list(metadata_df.columns)
    template_columns = [
        "source name", "assay name", "technology type", "characteristics[age]",
        "characteristics[ancestry category]",
        "characteristics[biological replicate]",
        "characteristics[cell line]",
        "characteristics[cell type]",
        "characteristics[developmental stage]",
        "characteristics[disease]",
        "characteristics[individual]",
        "characteristics[organism part]",
        "characteristics[organism]",
        "characteristics[sex]",
        "characteristics[enrichment process",
        "characteristics[compound]",
        "characteristics[concentration of compound]",
        "comment[modification parameters]",
        "comment[cleavage agent details]",
        "comment[data file]",
        "comment[fraction identifier]",
        "comment[fractionation method]",
        "comment[instrument]",
        "comment[label]",
        "comment[technical replicate]",
        "comment[fragment mass tolerance]",
        "comment[precursor mass tolerance]",
        "comment[dissociation method]",
        "characteristics[spiked compound]",
        "characteristics[synthetic peptide]",
        "characteristics[phenotype]",
        "comment[depletion]",
    ]
    value_columns=["source name", "assay name", "comment[data file]","comment[fraction identifier]","comment[technical replicate]"]
    other_columns = ["characteristics[sex]", "characteristics[age]"]

    # First narrow down the columns in the metadata file that are useful to match to the SDRF file
    sel, subm = st.columns(2)
    with sel:
        columns_to_match = st.multiselect(
            "Select columns containing data that will be used in the SDRF data",
            meta_columns,
        )
    with subm:
        submitbut = st.button('Match columns')
    mismatches = []
    if submitbut:
        st.session_state["matching"] = True

    if "matching" in st.session_state:
        col1, col2, col3, col4 = st.columns(4)

        selected_col = None
        matched_col = None
        for i in range(len(columns_to_match)):
            if not selected_col:
                with col1:
                    selected_col = st.selectbox(
                        f"Select column {i+1} to match in your metadata file:",
                        [""] + columns_to_match,
                        index=0,
                        key=f"selected_col{i}",
                    )
            if selected_col and not matched_col:
                with col2:
                    matched_col = st.selectbox(
                        f"Select the corresponding column from the SDRF file:",
                        ["", None] + template_columns,
                        index=0,
                        key=f"matched_col{i}",
                    )
                with col3:
                    check = st.button("Match and check ontology", key=f"check{i}")
                    st.write(" ")
                    st.write(" ")
                    st.write(" ")
                    if matched_col != None and check:
                        input_values = metadata_df[selected_col].unique()
                        input_values = [ i for i in input_values if i is not np.nan]
                        name = (matched_col.split('[')[-1].split(']')[0]).replace(' ', '_')
                        name = 'all_' + name + '_elements'
                        if matched_col in value_columns:
                                with col4:
                                    st.success('Great! The local metadata values are valid terms and are mapped to the SDRF file.', icon="✅")
                                template_df[matched_col] = metadata_df[selected_col]
                        elif matched_col in other_columns:
                            if matched_col == "characteristics[age]":
                                with col4:
                                    if ParsingModule.check_age_format(template_df, "characteristics[age]") == False:
                                        st.error("The age column is not in the correct format, please check and try again")
                                    elif ParsingModule.check_age_format(template_df, "characteristics[age]") == True:
                                        st.success('Great! The local metadata values are valid terms and are mapped to the SDRF file.', icon="✅")
                                        template_df[matched_col] = metadata_df[selected_col]
                            if matched_col == "characteristics[sex]":
                                #check if input_values only contains M, F or NA and no other strings or numbers
                                if all(x in ['M', 'F', 'NA'] for x in input_values):
                                    with col4:
                                        st.success('Great! The local metadata values are valid terms and are mapped to the SDRF file.', icon="✅")
                                    template_df[matched_col] = metadata_df[selected_col]
                                else:
                                    with col4:
                                        st.error("The sex column is not in the correct format. It should indiciate M, F or NA, please check and try again")

                        elif (matched_col not in value_columns) and name not in data_dict:
                            with col4:
                                st.error("This column does not contain ontology-based terms so this column cannot be matched. Please fill it in using the next steps in the sidebar")

                        else:
                            onto_elements = data_dict[name]
                            if matched_col == "characteristics[organism]":
                                map_organism_dict = {'Homo sapiens': ['Human', 'human', 'homo sapiens', 'Homo Sapiens'],
                                'Mus musculus': ['mouse', 'Mouse', 'Mus Musculus', 'mus musculus'],
                                'Arabidopsis thaliana': ['arabidopsis thaliana', 'Arabidopsis Thaliana', 'arabidopsis', 'Arabidopsis', 'thale cress'],
                                'Drosophila melanogaster': ['drosophila', 'Drosophila', 'Drosophila Melanogsaster', 'drosophila melanogaster', 'fruitfly', 'fruit fly'],
                                'Saccharomyces cerevisiae':['Saccharomyces Cerevisiae', 'saccharomyces cerevisiae', "brewer's yeast", "Brewer's yeast"],
                                'Caenorhabditis elegans':['C. Elegans', 'C. elegans', 'c. elegans', 'caenorhabditis elegans', 'Caenorhabditis Elegans', 'worm', 'Worm'],
                                'Danio rerio':['Danio Rerio', 'danio rerio', 'zebrafish', 'Zebrafish'],
                                'Escherichia coli': ['E. Coli', 'E. coli', 'e. coli', 'Escherichia Coli', 'escherichia coli']}
                                #dictionary containing the 3 most occuring organisms and all the ways they could be written
                                # if the input value contains one of the values in the list, it will be replaced by the key
                                # the value in the dataframe will be replaced by the key
                                for key, value in map_organism_dict.items():
                                    for i in input_values:
                                        if i in value:
                                            metadata_df[selected_col].replace(i, key, inplace=True)
                                            input_values[input_values.index(i)] = key
                            if not set(input_values).issubset(set(onto_elements)):
                                not_in_onto = set(input_values) - set(onto_elements)
                                mismatches.append(not_in_onto)
                                with col4:
                                    st.error(f'{not_in_onto} are not ontology terms. Select the correct terms in the next steps directly from the ontology', icon="❌")

                            elif (set(input_values).issubset(set(onto_elements))) and (len(input_values)>=1):
                                with col4:
                                    st.success('Great! The local metadata values are valid terms and are mapped to the SDRF file.' , icon="✅")
                                template_df[matched_col] = metadata_df[selected_col]
                        if matched_col == None:
                            with col4:
                                st.write("Skip this column")
                columns_to_match = [col for col in columns_to_match if col != selected_col]
                template_columns = [col for col in template_columns if col != matched_col]
                selected_col = None
                matched_col = None
