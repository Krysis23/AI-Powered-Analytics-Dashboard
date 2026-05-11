import plotly.express as px
import plotly.io as pio
import pandas as pd

def render_chart_json(df: pd.DataFrame, chart_type: str, x:str, y:str = None, color: str=None, title: str="") -> dict:
    ct = chart_type.lower()

    if ct == "bar":
        agg = df.groupby(x)[y].sum().reset_index().sort_values(y,ascending=False)
        fig = px.bar(agg, x=x, y=y, color=color, title=title)

    elif ct == "line":
        agg = df.groupby(x)[y].sum().reset_index().sort_values(x)
        fig = px.line(agg, x=x, y=y, color=color, title=title)
    elif ct == "scatter":
        fig = px.scatter(df,x=x, color=color, title=title)
    elif ct == "histogram":
        fig = px.histogram(df,x=x, color=color, title=title, nbins=30)
    elif ct == "box":
        fig = px.box(df,x=x, y=y, color=color, title=title)
    elif ct == "pie":
        agg = df.groupby(x)[y].sum().reset_index()
        fig = px.pie(agg,names=x,values=y,title=title)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")
    
    fig.update_layout(margin=dict(l=20,r=20,t=40,b=20), paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")

    return pio.to_json(fig)