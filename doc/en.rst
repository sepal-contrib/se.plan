se.plan
=======

Spatialy explicit, Socio-economic, sepal planning tool

Overview
--------

se.plan is a spatially explicit online tool designed to support forest restoration planning decisions by restoration stakeholders. It is part of the SEPAL (System for Earth Observation Data Access,
Processing and Analysis for Land Monitoring) component of UN FAO’s free, open-source software suite, Open Foris. It utilizes cloud-based supercomputing and geospatial datasets through Google Earth Engine. It aims to identify locations where the benefits of forest restoration are high relative to restoration costs, subject to biophysical and socioeconomic constraints that users impose to define the areas where restoration is allowable. As a decision-support tool, it is intended to be used in combination with other information users may have that provides greater detail on planning areas and features of those areas that se.plan might not adequately include. It offers users the option to replace its built-in data layers, which are based on publicly available global datasets, with users’ own customized layers. Please see Appendix A for a list of se.plan’s built-in data layers and their sources.

The sections below highlight key features of se.plan. A high-level view of using the tool can be described as follows: 
1.	Users start by (i) selecting their geographical planning area, (ii) rating the relative importance of different restoration benefits from their perspective, and (iii) imposing constraints that limit restoration to only those sites they view as suitable, in view of ecological and socioeconomic risks.
2.	se.plan then generates maps and related information on restoration’s benefits, costs, and risks for all suitable sites within the planning area. 
In addition to reading this manual, we encourage users to view se.plan YouTube videos at <add links>.

Geographical resolution and scope

se.plan divides the Earth’s surface into grid cells with 30 arc-second resolution (≈1km at the equator). It includes only grid cells that satisfy the following four criteria:
1.	They are in countries or territories of Africa and the Near East, Asia and the Pacific, and Latin America and the Caribbean that the World Bank classified as low- or middle-income countries or territories (LMICs) during most years during 2000–2020. These countries and territories number 139 and are listed in Appendix B.
2.	They include areas where tree cover can potentially occur under current climatic conditions, as determined by Bastin et al. (2019).
3.	Their current tree cover, as measured by the European Space Agency’s Copernicus Programme (Buchhorn et al. 2020), is less than their potential tree cover.
4.	They are not in urban use.
se.plan labels grid cells that satisfy these criteria potential restoration sites. It treats each grid cell as an independent restoration planning unit, with its own potential to provide restoration benefits and to entail restoration costs and risks.

Selection of planning area

se.plan offers users both a dropdown menu and a drawing feature to select their planning area, which se.plan labels the area of interest (AOI). The dropdown menu enables users to select a group of countries, an individual country, or one or more first-level administrative subdivisions (e.g., states or provinces) within a country. The drawing feature enables them to draw boundaries around up to two areas of their choosing.

Restoration benefits

Restoration offers many potential benefits. In its current form, se.plan provides information on four benefit categories:
1.	Biodiversity conservation
2.	Carbon sequestration
3.	Local livelihoods
4.	Wood production
se.plan includes two indicators each for biodiversity conservation and local livelihoods and one indicator each for carbon sequestration and wood production. Each indicator is associated with a data layer that estimates each grid cell’s relative potential to provide each benefit if the grid cell is restored, with the relative potential measured on a scale of 1 (low) to 5 (high). Please see Appendix C for more detail on the interpretation and generation of the data layers for the benefit indicators.

Users rate the relative importance of these benefits from their standpoint (or the standpoint of stakeholders they represent), and se.plan then calculates an index that indicates each grid cell’s relative restoration value aggregated across all four benefit categories. This restoration value index is a weighted average of the benefits, with user ratings serving as the weights. It therefore accounts for not only the potential of a grid cell to provide each benefit but also the relative importance that a user assigns to each benefit. It is scaled from 1 (low restoration value) to 5 (high restoration value). Please see Appendix D for more detail on the generation of the index.

Restoration costs

Forest restoration incurs two broad categories of costs, opportunity cost and implementation costs. 

Opportunity cost refers to the value of land if it is not restored to forest. se.plan assumes that the alternative land use would be some form of agriculture, either cropland or pasture. It sets the opportunity cost of potential restoration sites equal to the value of cropland for all sites where crops can be grown, with the opportunity cost for any remaining sites set equal to the value of pasture. Sites that cannot be used as either cropland or pasture are assigned an opportunity cost of zero. 

Implementation costs refer to the expense of activities required to regenerate forests on cleared land. They include both: (i) initial expenses incurred in the first year of restoration (establishment costs), which are associated with such activities as site preparation, planting, and fencing; and (ii) expenses associated with monitoring, protection, and other activities during the subsequent 3–5 years that are required to enable the regenerated stand to reach the “free to grow” stage (operating costs). 

se.plan assumes that implementation costs include planting expenses on all sites. This assumption might not be valid on sites where natural regeneration is feasible. To account for this possibility, se.plan includes a data layer that predicts the variability of natural regeneration success. 

se.plan calculates the overall restoration cost of each site by summing the corresponding estimates of the opportunity cost and implementation costs. Please see Appendix E for more detail on the interpretation and generation of the data layers for opportunity and implementation costs.

Benefit-cost ratio

se.plan calculates an approximate benefit-cost ratio for each site by dividing the restoration value index by the restoration cost and converting the resulting number to a scale from 1 (small ratio) to 5 (large ratio). Sites with a higher ratio are the ones that se.plan predicts are more suitable for restoration, subject to additional investigation that draws on other information users have on the sites. Please see Appendix D for more detail on the generation and interpretation of this ratio. A key limitation is that the ratio does not account interdependencies across sites related to either benefits, such as the impact of habitat scale on species extinction risk, or costs, such as scale economies in planting trees. This limitation stems from se.plan’s treatment of each potential restoration site as an independent restoration planning unit.

Constraints

se.plan allows users to impose constraints that limit restoration to only those sites they view as suitable, in view of ecological and socioeconomic risks. It groups the constraints into three categories:
1.	Biophysical (5 constraints): elevation, slope, annual rainfall, baseline water stress, terrestrial ecoregion
2.	Forest change (3 constraints): deforestation rate, climate risk, natural regeneration variability
3.	Socio-economic constraints (6 constraints): current land cover, protected areas, population density, declining population, property rights protection, accessibility to cities
se.plan includes sliders that users can adjust to exclude high, low, or both high and low values of most of these constraints. Some of the constraints are binary variables, with a value of 1 if a site has the characteristic associated with the site and 0 if it does not. For these constraints, users simply turn the constraint on or off, instead of using sliders. Please see Appendix F for more detail on the interpretation and generation of the data layers for the constraints.




 
Sections to be added, in addition to the indicated appendices:
1.	Output
2.	Customization
3.	Step-by-step guide for using se.plan
4.	Acknowledgments
5.	Contact information
Yelena, Pierrick, John, and Karis, I feel you are better placed than I to draft additional sections 1-3, while Yoshi and Yelena are better placed to draft additional sections 4-5. I am working on the appendices. Appendix A is in fact already done: it’s the list of primary data sources for default spatial layers we prepared in July.  













About
-----

Restoration of forests and other ecosystems can be a major nature-based strategy for achieving a wide range of global development goals and national priorities, including Sustainable Development Goals, but the suitability of different locations for restoration varies and financial resources are limited. Country governments, international organizations, and other restoration stakeholders need to identify and prioritize locations suitable for restoration. A suitability analysis for forest restoration requires information on not only ecological conditions for tree growth but also restoration’s socioeconomic impacts, including its benefits, costs, and risks. Locations where benefits are high relative to costs and risks are where restoration is more likely to achieve sustainable success. These locations are also where restoration initiatives are more likely to attract the private investment needed to augment government funding and official development assistance.
  
This mapping tool combines ecological data on forest restoration with data on restorations’s benefits, costs, and risks. It is intended to support the preparation of strategic restoration plans for a given area of interest (AOI) —a country, a group of countries, or a region within a country—by providing spatially explicit information on restoration suitability and impacts. This information is intended to aid decision makers in identifying promising, cost-effective restoration locations: locations where restoration provides a high level of benefits relative to the costs incurred. It can also help identify tradeoffs among impacts that might require further attention.  
  
Before running the tool, users select their areas of interest, provide information on their ratings of different prospective restoration benefits (i.e., the relative importance of the benefits to them), and have the option to impose constraints that exclude locations they view as unsuitable for restoration due to ecological or socioeconomic risks. The tool then generates maps and related information on restoration’s benefits, costs, and risks in the areas of interest. It provides an overall suitability index, on a scale of 1 to 5, that indicates the relative benefit-cost ratio for each location within the areas of interest. By varying the benefit ratings and constraints, users can investigate the sensitivity of model output to these input choices. They also have the option to use customized data for their areas of interest instead of the default data build into the tool.

.. image:: https://raw.githubusercontent.com/12rambau/restoration_planning_module/master/utils/light/duke.png
    :alt: duke_logo
    :height: 100
    :target: https://duke.edu
    
.. image:: https://raw.githubusercontent.com/12rambau/restoration_planning_module/master/utils/light/peking.png
    :alt: pku_logo
    :height: 100
    :target: http://english.pku.edu.cn
    
.. image:: https://raw.githubusercontent.com/12rambau/restoration_planning_module/master/utils/light/sig.png
    :alt: sig-gis_logo
    :height: 100
    :target: https://sig-gis.com
    
.. image:: https://raw.githubusercontent.com/12rambau/restoration_planning_module/master/utils/light/SilvaCarbon.png
    :alt: silvacarbon_logo
    :height: 100
    :target: https://www.silvacarbon.org
    
.. image:: https://raw.githubusercontent.com/12rambau/restoration_planning_module/master/utils/light/MAFF.png
    :alt: MAFF_logo
    :height: 100
    :target: https://www.maff.go.jp/e/
    
.. Warning::

    The usage and method documentation are in elaboration
