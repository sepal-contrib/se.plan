# se.plan Workflow

High-level diagram of the user workflow in se.plan, from opening the app to producing a suitability map and dashboard.

```mermaid
flowchart TD
    Start([User opens se.plan]) --> Recipe{Recipe}
    Recipe -->|New| NewRecipe[Initialize default recipe]
    Recipe -->|Load| LoadRecipe[Load recipe from file]
    NewRecipe --> AOI
    LoadRecipe --> AOI

    AOI[/"Define AOI<br/>(admin / draw / shapefile / GEE asset)"/]
    AOI --> ValidateAOI{Within LMIC?}
    ValidateAOI -->|No| AOI
    ValidateAOI -->|Yes| Questionnaire

    Questionnaire[/"Answer Questionnaire"/]
    Questionnaire --> Benefits[Benefits<br/>weighted criteria]
    Questionnaire --> Constraints[Constraints<br/>binary mask]
    Questionnaire --> Costs[Costs<br/>weighted factors]

    Benefits --> RecipeModel[(Recipe model<br/>seplan_aoi + benefit + constraint + cost)]
    Constraints --> RecipeModel
    Costs --> RecipeModel

    RecipeModel --> Compute[["Seplan engine<br/>get_constraint_index()"]]

    Compute --> SuitabilityMap[/"Suitability Map<br/>(raster on map)"/]
    Compute --> Dashboard[/"Dashboard<br/>(charts + stats)"/]

    SuitabilityMap --> Outputs
    Dashboard --> Outputs
    Outputs([Download / Save / Compare])

    Outputs -.optional.-> SubAOI[Custom sub-AOIs]
    Outputs -.optional.-> CompareScenarios[Compare scenarios<br/>load multiple recipes]
    SubAOI --> Compute
    CompareScenarios --> SuitabilityMap

    classDef stage fill:#e1f5ff,stroke:#0288d1
    classDef output fill:#fff3e0,stroke:#f57c00
    classDef model fill:#f3e5f5,stroke:#7b1fa2
    class AOI,Questionnaire stage
    class SuitabilityMap,Dashboard,Outputs output
    class RecipeModel model
```

## Stages

1. **Recipe** — create a new recipe or load an existing one. The recipe is the central data model holding AOI, benefits, constraints, and costs.
2. **Define AOI** — pick a study area via admin boundaries, drawing, shapefile, or a GEE asset. Validated against LMIC scope.
3. **Questionnaire** — weight benefits and costs and pick constraints (binary mask) for the analysis.
4. **Compute** — the Seplan engine combines benefits, constraints, and costs into a suitability index.
5. **Outputs** — suitability map (raster) and dashboard (charts + stats), available for download.
6. **Optional** — refine with custom sub-AOIs, or compare multiple recipes side by side.
