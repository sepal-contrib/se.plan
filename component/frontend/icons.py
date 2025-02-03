icons = {
    "clock": {
        "fa": "fa-solid fa-clock",
        "mdi": "mdi-clock-alert",
    },
    "checkbox-marked-circle": {
        "fa": "fa-solid fa-circle-check",
        "mdi": "mdi-checkbox-marked-circle",
    },
    "swap-horizontal": {
        "fa": "fa-solid fa-right-left",
        "mdi": "mdi-swap-horizontal",
    },
    "plus": {
        "fa": "fa-solid fa-plus",
        "mdi": "mdi-plus",
    },
    "map": {
        "fa": "fa-solid fa-map",
        "mdi": "mdi-map",
    },
    "broom": {
        "fa": "fa-solid fa-broom",
        "mdi": "mdi-broom",
    },
    "compare": {
        "fa": "fa-solid fa-scale-unbalanced",
        "mdi": "mdi-compare",
    },
    "close": {
        "fa": "fa-solid fa-xmark",
        "mdi": "mdi-close",
    },
    "help-circle": {
        "fa": "fa-regular fa-circle-question",
        "mdi": "mdi-help-circle-outline",
    },
    "save": {
        "fa": "fa-solid fa-floppy-disk",
        "mdi": "mdi-content-save",
    },
    "check": {
        "fa": "fa-solid fa-check",
        "mdi": "mdi-check",
    },
    "pencil": {
        "fa": "fa-solid fa-pencil",
        "mdi": "mdi-pencil",
    },
    "trash-can": {
        "fa": "fa-solid fa-trash",
        "mdi": "mdi-trash-can",
    },
    "draw": {
        "fa": "fa-solid fa-draw-polygon",
        "mdi": "mdi-draw",
    },
    "wrench": {
        "fa": "fa-solid fa-wrench",
        "mdi": "mdi-wrench",
    },
    "circle": {
        "fa": "fa-solid fa-circle",
        "mdi": "mdi-circle",
    },
    "recipe-note": {
        "fa": "fa-solid fa-file-lines",
        "mdi": "mdi-note-text",
    },
    "upload": {
        "fa": "fa-solid fa-upload",
        "mdi": "mdi-upload",
    },
    "dashboard": {
        "fa": "fa-solid fa-chart-simple",
        "mdi": "mdi-view-dashboard",
    },
    "location": {
        "fa": "fa-solid fa-location-dot",
        "mdi": "mdi-map-marker-check",
    },
    "question-file": {
        "fa": "fa-solid fa-file-circle-question",
        "mdi": "mdi-file-question",
    },
}


def icon(icon: str, lib: str = "mdi") -> str:
    """Return the icon class."""

    return icons[icon][lib]
