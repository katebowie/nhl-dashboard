importScripts("https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide...");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded pyodide!");
  const data_archives = [];
  for (const archive of data_archives) {
    let zipResponse = await fetch(archive);
    let zipBinary = await zipResponse.arrayBuffer();
    self.postMessage({type: 'status', msg: `Unpacking ${archive}`})
    self.pyodide.unpackArchive(zipBinary, "zip");
  }
  await self.pyodide.loadPackage("micropip");
  self.postMessage({type: 'status', msg: `Installing environment`})
  try {
    await self.pyodide.runPythonAsync(`
      import micropip
      await micropip.install(['https://cdn.holoviz.org/panel/wheels/bokeh-3.9.0-py3-none-any.whl', 'https://cdn.holoviz.org/panel/1.8.10/dist/wheels/panel-1.8.10-py3-none-any.whl', 'pyodide-http', 'data', 'pandas']);
    `);
  } catch(e) {
    console.log(e)
    self.postMessage({
      type: 'status',
      msg: `Error while installing packages`
    });
  }
  console.log("Environment loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(`\nimport asyncio\n\nfrom panel.io.pyodide import init_doc, write_doc\n\ninit_doc()\n\nimport panel as pn\nimport pandas as pd\nfrom data.fetch_data import get_standings, get_all_remaining_schedules\nfrom data.process_data import add_team_metrics, add_ranking, simulate_season\n\npn.extension('tabulator', theme="dark")\n\n# \u2500\u2500 Loading screen \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\nloading = pn.indicators.LoadingSpinner(value=True, size=50)\nmain_content = pn.Column(\n    "# NHL Playoff Simulations",\n    "### Loading latest NHL data... this may take up to 30 seconds",\n    loading\n)\n\n# \u2500\u2500 Helper functions \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\ndef color_rows(row):\n    if row["Div Rank"] <= 3:\n        return ["background-color: rgba(26, 71, 42, 0.6); color: white"] * len(row)\n    elif row["WC Rank"] <= 5:\n        return ["background-color: rgba(122, 92, 0, 0.6); color: white"] * len(row)\n    else:\n        return ["background-color: rgba(107, 26, 26, 0.6); color: white"] * len(row)\n\ndef make_table(data):\n    data = data.copy()\n    # Store raw float in hidden column for coloring\n    data["_prob"] = data["Playoff %"]\n    # Convert to percentage string for display\n    data["Playoff %"] = (data["Playoff %"] * 100).round(1).astype(str) + "%"\n    # Apply colors using hidden column\n    styled = data.style.apply(color_rows, axis=1)\n    return pn.widgets.Tabulator(\n    styled,\n    pagination="local",\n    page_size=20,\n    sizing_mode="stretch_width",\n    theme="midnight",\n    hidden_columns=["WC Rank", "_prob"]\n)\n\ndef make_display_df(data):\n    df = data[[\n        "team", "points", "division", "division_rank", "wildcard_rank", "playoff_prob"\n    ]].copy()\n    df.columns = ["Team", "Points", "Division", "Div Rank", "WC Rank", "Playoff %"]\n    df["WC Rank"] = df["WC Rank"].fillna(999)\n    df = df.reset_index(drop=True)\n    return df\n\n# \u2500\u2500 Data loading \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\ndef load_data():\n    df = get_standings()\n    df = add_team_metrics(df)\n    df = add_ranking(df)\n    schedule = get_all_remaining_schedules(df)\n    probs = simulate_season(df, schedule)\n    df = df.merge(probs, on="team_abbrev", how="left")\n\n    display_df = make_display_df(df)\n\n    all_table = make_table(display_df.drop(columns="Division").sort_values("Playoff %", ascending=False))\n\n    atlantic_table = make_table(display_df[display_df["Division"] == "Atlantic"].drop(columns="Division").sort_values("Div Rank"))\n    metro_table = make_table(display_df[display_df["Division"] == "Metropolitan"].drop(columns="Division").sort_values("Div Rank"))\n    central_table = make_table(display_df[display_df["Division"] == "Central"].drop(columns="Division").sort_values("Div Rank"))\n    pacific_table = make_table(display_df[display_df["Division"] == "Pacific"].drop(columns="Division").sort_values("Div Rank"))\n\n    dashboard = pn.Tabs(\n        ("All Teams", pn.Column("## All Teams", all_table)),\n        ("Atlantic", pn.Column("## Atlantic Division", atlantic_table)),\n        ("Metropolitan", pn.Column("## Metropolitan Division", metro_table)),\n        ("Central", pn.Column("## Central Division", central_table)),\n        ("Pacific", pn.Column("## Pacific Division", pacific_table)),\n        styles={"background": "#1a1a2e", "padding": "20px"}\n    )\n\n    main_content.clear()\n    main_content.append(dashboard)\n    print("Dashboard loaded!")\n\npn.state.onload(load_data)\nmain_content.servable()\n\nawait write_doc()`)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.globals.set('patch', msg.patch)
    self.pyodide.runPythonAsync(`
    from panel.io.pyodide import _convert_json_patch
    state.curdoc.apply_json_patch(_convert_json_patch(patch), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.globals.set('location', msg.location)
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads(location)
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()