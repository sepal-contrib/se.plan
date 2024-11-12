import solara

# solara.server.settings.assets.fontawesome_path = "/font-awesome/6.2.1/css/all.min.css"
# solara.server.settings.assets.extra_locations = ["./assets/"]
# solara.settings.assets.cdn = "https://cdnjs.cloudflare.com/ajax/libs/"
# solara.server.settings.main.base_url = "/api/app-launcher/seplan/"


@solara.component
def Page():
    with solara.Sidebar():
        with solara.Card("Sidebar of page 1", margin=0, elevation=0):
            solara.Markdown("Hi there 👋!")
            solara.Button(
                label="View source",
                icon_name="mdi-github-circle",
                attributes={"href": "github_url", "target": "_blank"},
                text=True,
                outlined=True,
            )
