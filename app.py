"""
SQL Data Warehouse Analytics Dashboard
A lightweight Streamlit application for exploring warehouse data
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os

# Page Configuration
st.set_page_config(
    page_title="Data Warehouse Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
    <style>
        .metric-card { padding: 20px; border-radius: 10px; }
        h1 { color: #1f77b4; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# FUNCTIONS
# ============================================================================

@st.cache_data
def load_csv_files():
    """Dynamically load all CSV files from datasets folder"""
    datasets = {}
    data_path = Path(__file__).parent / "datasets"
    
    # Load from source_crm and source_erp
    for folder in ["source_crm", "source_erp"]:
        folder_path = data_path / folder
        if folder_path.exists():
            for file in folder_path.glob("*.csv"):
                try:
                    df = pd.read_csv(file, low_memory=False)
                    source_name = f"{folder.upper()} - {file.stem}"
                    datasets[source_name] = df
                except Exception as e:
                    st.error(f"Error loading {file.name}: {e}")
    
    return datasets


def get_numeric_columns(df):
    """Get numeric columns from dataframe"""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df):
    """Get categorical columns from dataframe"""
    return df.select_dtypes(include=['object']).columns.tolist()


def create_kpi_cards(df, numeric_cols):
    """Create KPI metric cards"""
    if not numeric_cols:
        return
    
    cols = st.columns(len(numeric_cols[:4]))  # Max 4 KPIs
    
    for idx, col in enumerate(numeric_cols[:4]):
        with cols[idx]:
            value = df[col].sum()
            mean_val = df[col].mean()
            st.metric(
                label=col.title(),
                value=f"{value:,.0f}",
                delta=f"Avg: {mean_val:,.0f}"
            )


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("🎛️ Controls")

datasets = load_csv_files()

if not datasets:
    st.error("❌ No CSV files found in datasets/source_crm/ or datasets/source_erp/")
    st.stop()

# Dataset Selection
selected_dataset = st.sidebar.selectbox(
    "📊 Select Dataset",
    options=list(datasets.keys()),
    help="Choose a CSV file to explore"
)

df = datasets[selected_dataset]

# Column Selection
all_columns = df.columns.tolist()
selected_columns = st.sidebar.multiselect(
    "🏷️ Select Columns",
    options=all_columns,
    default=all_columns[:5] if len(all_columns) > 5 else all_columns,
    help="Choose columns to display and analyze"
)

if not selected_columns:
    selected_columns = all_columns

df_filtered = df[selected_columns].copy()

# Filters
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filters")

numeric_cols = get_numeric_columns(df_filtered)
categorical_cols = get_categorical_columns(df_filtered)

# Apply categorical filters
filters_applied = {}
for col in categorical_cols[:3]:  # Limit to 3 categorical filters
    unique_vals = df_filtered[col].unique()
    if len(unique_vals) <= 20:
        selected_vals = st.sidebar.multiselect(
            f"{col}",
            options=unique_vals,
            default=unique_vals,
            key=f"filter_{col}"
        )
        if selected_vals:
            filters_applied[col] = selected_vals

# Apply numeric range filters
for col in numeric_cols[:2]:  # Limit to 2 numeric filters
    min_val = float(df_filtered[col].min())
    max_val = float(df_filtered[col].max())
    range_vals = st.sidebar.slider(
        f"{col} Range",
        min_val,
        max_val,
        (min_val, max_val),
        key=f"range_{col}"
    )
    if range_vals[0] > min_val or range_vals[1] < max_val:
        df_filtered = df_filtered[
            (df_filtered[col] >= range_vals[0]) &
            (df_filtered[col] <= range_vals[1])
        ]

# Apply categorical filters
for col, values in filters_applied.items():
    df_filtered = df_filtered[df_filtered[col].isin(values)]

# Search functionality
st.sidebar.markdown("---")
search_term = st.sidebar.text_input("🔎 Search", placeholder="Search in data...")
if search_term:
    mask = df_filtered.astype(str).apply(
        lambda x: x.str.contains(search_term, case=False, na=False)
    ).any(axis=1)
    df_filtered = df_filtered[mask]


# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title(f"📊 {selected_dataset}")

# Dataset Info
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📈 Rows", f"{len(df_filtered):,}")
with col2:
    st.metric("🏷️ Columns", len(selected_columns))
with col3:
    st.metric("💾 Size (KB)", f"{df_filtered.memory_usage(deep=True).sum() / 1024:.1f}")
with col4:
    st.metric("🔍 Null Values", int(df_filtered.isnull().sum().sum()))

st.divider()

# KPI Cards (if numeric data exists)
if numeric_cols:
    st.subheader("📊 Key Metrics")
    create_kpi_cards(df_filtered, numeric_cols)
    st.divider()

# Data Display Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📋 Table", "📈 Charts", "📊 Statistics", "💾 Download", "📑 Info"]
)

# ============================================================================
# TAB 1: TABLE VIEW
# ============================================================================

with tab1:
    st.subheader("Data Table")
    
    # Pagination
    col1, col2 = st.columns([3, 1])
    with col2:
        rows_to_show = st.selectbox(
            "Rows per page",
            [10, 25, 50, 100],
            label_visibility="collapsed"
        )
    
    # Display table
    st.dataframe(
        df_filtered.head(rows_to_show),
        use_container_width=True,
        height=500
    )
    
    st.info(f"Showing {min(rows_to_show, len(df_filtered))} of {len(df_filtered)} rows")


# ============================================================================
# TAB 2: CHARTS
# ============================================================================

with tab2:
    st.subheader("Visualizations")
    
    if not numeric_cols:
        st.warning("No numeric columns available for visualization")
    else:
        col1, col2 = st.columns(2)
        
        # Chart Type Selection
        with col1:
            chart_type = st.selectbox(
                "📊 Chart Type",
                ["Bar", "Line", "Histogram", "Pie", "Scatter"]
            )
        
        # Column Selection for X and Y
        with col2:
            if chart_type != "Pie":
                x_col = st.selectbox("X-Axis", all_columns)
                y_col = st.selectbox("Y-Axis", numeric_cols)
            else:
                y_col = st.selectbox("Values", numeric_cols)
                x_col = st.selectbox("Labels", categorical_cols if categorical_cols else all_columns)
        
        st.divider()
        
        # Create Charts
        try:
            if chart_type == "Bar":
                agg_data = df_filtered.groupby(x_col)[y_col].sum().reset_index()
                fig = px.bar(agg_data, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Line":
                agg_data = df_filtered.groupby(x_col)[y_col].mean().reset_index()
                fig = px.line(agg_data, x=x_col, y=y_col, markers=True, title=f"{y_col} Trend")
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Histogram":
                fig = px.histogram(df_filtered, x=y_col, nbins=30, title=f"Distribution of {y_col}")
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Pie":
                agg_data = df_filtered.groupby(x_col)[y_col].sum().reset_index()
                fig = px.pie(agg_data, values=y_col, names=x_col, title=f"Composition by {x_col}")
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Scatter":
                if len(numeric_cols) >= 2:
                    y_col2 = st.selectbox("Y2-Axis", numeric_cols, key="y2")
                    fig = px.scatter(df_filtered, x=y_col, y=y_col2, title=f"{y_col} vs {y_col2}")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Need at least 2 numeric columns for scatter plot")
        
        except Exception as e:
            st.error(f"Error creating chart: {e}")


# ============================================================================
# TAB 3: STATISTICS
# ============================================================================

with tab3:
    st.subheader("Statistical Summary")
    
    if numeric_cols:
        stats_df = df_filtered[numeric_cols].describe().T
        st.dataframe(stats_df, use_container_width=True)
    else:
        st.info("No numeric columns to summarize")
    
    # Data Quality Info
    st.subheader("Data Quality")
    quality_data = {
        "Metric": ["Total Rows", "Missing Values", "Duplicate Rows", "Completeness %"],
        "Value": [
            len(df_filtered),
            int(df_filtered.isnull().sum().sum()),
            int(df_filtered.duplicated().sum()),
            f"{(1 - df_filtered.isnull().sum().sum() / (len(df_filtered) * len(df_filtered.columns))) * 100:.1f}%"
        ]
    }
    st.dataframe(pd.DataFrame(quality_data), use_container_width=True, hide_index=True)


# ============================================================================
# TAB 4: DOWNLOAD
# ============================================================================

with tab4:
    st.subheader("💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    # CSV Export
    with col1:
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"{selected_dataset.replace(' - ', '_')}_filtered.csv",
            mime="text/csv"
        )
    
    # Excel Export
    with col2:
        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False)
            buffer.seek(0)
            st.download_button(
                label="📥 Download as Excel",
                data=buffer.getvalue(),
                file_name=f"{selected_dataset.replace(' - ', '_')}_filtered.xlsx",
                mime="application/vnd.ms-excel"
            )
        except ImportError:
            st.info("Install openpyxl to export as Excel: `pip install openpyxl`")
    
    st.divider()
    
    # Summary Statistics Export
    st.subheader("Summary Statistics")
    if numeric_cols:
        summary = df_filtered[numeric_cols].describe().T
        summary_csv = summary.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Download Statistics as CSV",
            data=summary_csv,
            file_name=f"{selected_dataset.replace(' - ', '_')}_statistics.csv",
            mime="text/csv"
        )


# ============================================================================
# TAB 5: INFORMATION
# ============================================================================

with tab5:
    st.subheader("📑 Dataset Information")
    
    # Column Information
    st.write("**Columns:**")
    col_info = pd.DataFrame({
        "Column": df_filtered.columns,
        "Type": [str(dtype) for dtype in df_filtered.dtypes],
        "Non-Null": [df_filtered[col].notna().sum() for col in df_filtered.columns],
        "Null": [df_filtered[col].isna().sum() for col in df_filtered.columns]
    })
    st.dataframe(col_info, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Sample Data
    st.write("**Sample Data (First 5 Rows):**")
    st.dataframe(df_filtered.head(5), use_container_width=True)


# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
    <small style='text-align: center; color: gray;'>
    📊 SQL Data Warehouse Analytics Dashboard | Built with Streamlit & Plotly
    </small>
""", unsafe_allow_html=True)
