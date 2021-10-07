se.plan
=======

Introduction
------------

Overview
^^^^^^^^

**se.plan** is a spatially explicit online tool designed to support forest restoration planning decisions by restoration stakeholders. It is part of `SEPAL <https://sepal.io/>`_ (System for Earth Observation Data Access, Processing and Analysis for Land Monitoring), a component of UN FAO’s free, open-source software suite, `Open Foris <http://www.openforis.org>`_. It aims to identify locations where the benefits of forest restoration are high relative to restoration costs, subject to biophysical and socioeconomic constraints that users impose to define the areas where restoration is allowable. The computation is performed using cloud-based supercomputing and geospatial datasets from Google Earth Engine available through SEPAL. As a decision-support tool, it is intended to be used in combination with other information users may have that provides greater detail on planning areas and features of those areas that **se.plan** might not adequately include. It offers users the option to replace its built-in data layers, which are based on publicly available global datasets, with users’ own customized layers. Please see :ref:`Appendix A <#>` for a list of **se.plan**’s built-in data layers and their sources.

The sections below highlight key features of **se.plan**. A high-level view of using the tool can be described as follows: 

.. rst-class:: center

    Users start by (i) selecting their geographical planning area, (ii) rating the relative importance of different restoration benefits from their perspective, and (iii) imposing constraints that limit restoration to only those sites they view as suitable, in view of ecological and socioeconomic risks. **se.plan** then generates maps and related information on restoration’s benefits, costs, and risks for all suitable sites within the planning area. 

In addition to reading this manual, we encourage users to watch **se.plan** YouTube videos: `video being shot <#>`_.

Geographical resolution and scope
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**se.plan** divides the Earth’s surface into grid cells with 30 arc-second resolution (≈1km at the equator). It includes only grid cells that satisfy the following four criteria:

-   They are in countries or territories of Africa and the Near East, Asia and the Pacific, and Latin America and the Caribbean that the World Bank classified as *low or middle-income countries* or territories (LMICs) during most years during 2000–2020. These countries and territories number 139 and are listed in :ref:`Appendix B <#>`.
-   They include areas where tree cover can potentially occur under current climatic conditions, as determined by `Bastin et al. (2019) <https://doi.org/10.1126/science.aax0848>`_.
-   Their current tree cover, as measured by the European Space Agency’s Copernicus Programme (`Buchhorn et al. 2020 <https://doi.org/10.3390/rs12061044>`_), is less than their potential tree cover.
-   They are not in urban use.

**se.plan** labels grid cells that satisfy these criteria potential restoration sites. It treats each grid cell as an independent restoration planning unit, with its own potential to provide restoration benefits and to entail restoration costs and risks.

Methodology
-----------

Selection of planning area
^^^^^^^^^^^^^^^^^^^^^^^^^^

**se.plan** offers users multiple ways to select their planning area, which **se.plan** labels as *Area Of Interest* (AOI) as described in the :ref:`Usage section <#>`. 

Restoration indicators
^^^^^^^^^^^^^^^^^^^^^^

Restoration offers many potential benefits. In its current form, **se.plan** provides information on four benefit categories:

-   Biodiversity conservation
-   Carbon sequestration
-   Local livelihoods
-   Wood production

**se.plan** includes two indicators each for biodiversity conservation and local livelihoods and one indicator each for carbon sequestration and wood production. Each indicator is associated with a data layer that estimates each grid cell’s relative potential to provide each benefit if the grid cell is restored;  the relative potential is measured on a scale of 1 (low) to 5 (high). Please see :ref:`Appendix C <#>` for more detail on the interpretation and generation of the data layers for the benefit indicators.

Users rate the relative importance of these benefits from their standpoint (or the standpoint of stakeholders they represent), and **se.plan** then calculates an index that indicates each grid cell’s relative restoration value aggregated across all four benefit categories. This restoration value index is a weighted average of the benefits, with user ratings serving as the weights. It therefore accounts for not only the potential of a grid cell to provide each benefit but also the relative importance that a user assigns to each benefit. It is scaled from 1 (low restoration value) to 5 (high restoration value). Please see Appendix D for more detail on the generation of the index.

Restoration cost
^^^^^^^^^^^^^^^^

Forest restoration incurs two broad categories of costs, **opportunity cost** and **implementation costs**. 

**Opportunity cost** refers to the value of land if it is not restored to forest. **se.plan** assumes that the alternative land use would be some form of agriculture, either cropland or pasture. It sets the opportunity cost of potential restoration sites equal to the value of cropland for all sites where crops can be grown, with the opportunity cost for any remaining sites set equal to the value of pasture. Sites that cannot be used as either cropland or pasture are assigned an opportunity cost of zero. 

**Implementation costs** refer to the expense of activities required to regenerate forests on cleared land. They include both: (i) initial expenses incurred in the first year of restoration (establishment costs), which are associated with such activities as site preparation, planting, and fencing; and (ii) expenses associated with monitoring, protection, and other activities during the subsequent 3–5 years that are required to enable the regenerated stand to reach the “free to grow” stage (operating costs). 

**se.plan** assumes that implementation costs include planting expenses on all sites. This assumption might not be valid on sites where natural regeneration is feasible. To account for this possibility, **se.plan** includes a data layer that predicts the variability of natural regeneration success. 

**se.plan** calculates the overall restoration cost of each site by summing the corresponding estimates of the opportunity cost and implementation costs. Please see Appendix E for more detail on the interpretation and generation of the data layers for opportunity and implementation costs.

Benefit-cost ratio
^^^^^^^^^^^^^^^^^^

**se.plan** calculates an approximate benefit-cost ratio for each site by dividing the restoration value index by the restoration cost and converting the resulting number to a scale from 1 (small ratio) to 5 (large ratio). Sites with a higher ratio are the ones that **se.plan** predicts are more suitable for restoration, subject to additional investigation that draws on other information users have on the sites. Please see :ref:`Appendix D` for more detail on the generation and interpretation of this ratio. A key limitation is that the ratio does not account interdependencies across sites related to either benefits, such as the impact of habitat scale on species extinction risk, or costs, such as scale economies in planting trees. This limitation stems from **se.plan**’s treatment of each potential restoration site as an independent restoration planning unit.

Constraint
^^^^^^^^^^

**se.plan** allows users to impose constraints that limit restoration to only those sites they view as suitable, in view of ecological and socioeconomic risks. It groups the constraints into four categories:

-   Biophysical (5 constraints): elevation, slope, annual rainfall, baseline water stress, terrestrial ecoregion
-   Current land cover (5 constraints): Shrub land, Herbaceous vegetation, Agricultural land, Urban / built up, Bare / sparse vegetation, Snow and ice, Herbaceous wetland, Moss and lichen
-   Forest change (3 constraints): deforestation rate, climate risk, natural regeneration variability
-   Socio-economic constraints (6 constraints): protected areas, population density, declining population, property rights protection, accessibility to cities

**se.plan** enables the user to adjust the values that will be masked from the analysis for most of these constraints. Some of the constraints are binary variables, with a value of 1 if a site has the characteristic associated with the variable and 0 if it does not. For these constraints, users can choose if they want to keep zeros or ones.

Please see :ref:`Appendix F <#>` for more detail on the interpretation and generation of the data layers for the constraints.

Customization
^^^^^^^^^^^^^

Every Constraints and benefits are based on layers provided within the tools. These layer may not be covering the AOI selected by the user or provide less accurate/updated data than the National datasets available. To allow user to improve the quality of the analysis **se.plan** provides the possiblity of replacing these datasets by any layer available with Google Earth Engine.

Please see :ref:`Usage <#>`for more details on the customization process.

Output
^^^^^^

The output provides two outputs: 

- A map of the Restoration suitability index scaled from 1 (low suitability) to 5 (high suitability). This map, generated within the Google Earth Engine API can be displayed in the app but also exported as a GEE asset or a .tif file in your SEPAL folders. 

- A dashboard that summarize informations on the AOI and sub-AOIs defined by the users. The suitability index is thus presented as surfaces in Mha but **se.plan** also displays the mean values of the benefits and the sum of all the used constraints and cost over the AOIs.


.. _Appendix F:

Constraints data layers
-----------------------

se.plan includes various constraints that enable users to restrict restoration to sites that satisfy specific criteria. Many of the constraints can be viewed as indicators of risk, which allows users to avoid sites where the risk of failure, or the risk of undesirable impacts, might be unacceptable. Values of the constraints should be viewed as average values for a site, with some locations within a site likely having higher or lower values. The constraints are grouped into faour categories: biophysical, current land cover, forest change, and socio-economic.

Biophysical constraints
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :header-rows: 1
    
    * - Variable
      - Units
      - Description
      - Source
    * - Elevation
      - meters
      - Void-filled digital elevation dataset from Shuttle Radar Topography Mission (SRTM).
      - T.G. Farr, P.A. Rosen, E. Caro, et al., 2007, The shuttle radar topography mission: Reviews of Geophysics, v. 45, no. 2, RG2004, at https://doi.org/10.1029/2005RG000183.
    * - Slope
      - degrees
      - The elevation dataset (see above) was used to calculate slope in units of degrees from horizontal, with greater values indicating steeper inclines.
      - T.G. Farr, P.A. Rosen, E. Caro, et al., 2007, The shuttle radar topography mission: Reviews of Geophysics, v. 45, no. 2, RG2004, at https://doi.org/10.1029/2005RG000183.
    * - Annual rainfall
      - mm/yr
      - High-resolution estimates of total annual rainfall based on blending satellite information with station data and regression-based spatial interpolation.
      - C. Funk, P. Peterson, M. Landsfeld, et al., The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes. Sci Data 2, 150066. https://doi.org/10.1038/sdata.2015.66 
    * - Baseline water stress
      - scale (0 to 5)
      - Ratio of total water withdrawals (for consumptive and nonconsumptive domestic, industrial, irrigation, and livestock uses) to available renewable supplies of surface water and groundwater, averaged across months of the year and converted to a numerical scale. Higher values of the scale indicate greater water stress.
      - World Resources Institute, 2021, Aqueduct Global Maps 3.0 Data, https://www.wri.org/data/aqueduct-global-maps-30-data 

Current land cover
^^^^^^^^^^^^^^^^^^

.. list-table::
    :header-rows: 1
    
    * - Variable
      - Units
      - Description
      - Source
    * - Terrestrial ecoregion
      - ecological zone labels
      - Classification of Earth’s land surface into 20 ecological zones, which have relatively homogeneous vegetation formations under natural conditions and similar physical features (e.g., climate)
      - UN FAO, 2012 Global ecological zones for fao forest reporting: 2010 Update, http://www.fao.org/3/ap861e/ap861e.pdf 


Forest change constraints
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :header-rows: 1
    
    * - Variable
      - Units
      - Description
      - Source
    * - Deforestation rate
      - %/yr
      - Annual rate of tree-cover loss within a 5 km buffer around a site during 2005–2015, expressed as a positive percentage of total tree cover. Higher values indicate higher rates of loss. The value is zero in areas without deforestation (i.e., areas with expanding tree cover).
      - Developed by **se.plan** team, using data from: ESA, 2017, Land Cover CCI Product User Guide, Version 2, `maps.elie.ucl.ac.be/CCI/viewer/download/ESACCI-LC-Ph2-PUGv2_2.0.pd`_  
      - Climate risk
      - % of area
      - Difference between potential tree cover in 2050 if climate trends continue, and potential tree cover under current climatic conditions. Positive values indicate increases in potential tree cover, while negative values indicate decreases.
      - J.F. Bastin, Y. Finegold, C. Garcia, et al., 2019, The global tree restoration potential, Science 365(6448), pp. 76–79, DOI: 10.1126/science.aax0848; data downloaded from: https://www.research-collection.ethz.ch/handle/20.500.11850/350258 
    * - Natural regeneration variability
      - scale (0 to 1)
      - Measure of variability of forest restoration in fostering recovery of biodiversity to typical levels in natural native forests. Higher values indicate that biodiversity recovery is more variable (i.e., less predictable).
      - Developed by se.plan team, using model from: R. Crouzeilles, F.S. Barros, P.G. Molin, et al., 2019, A new approach to map landscape variation in forest restoration success in tropical and temperate forest biomes, J Appl Ecol. 56, pp. 2675– 2686, https://doi.org/10.1111/1365-2664.13501; and data from: ESA, 2017, Land Cover CCI Product User Guide, Version 2, maps.elie.ucl.ac.be/CCI/viewer/download/ESACCI-LC-Ph2-PUGv2_2.0.pdf 

Socio-economic constraints
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :header-rows: 1
    
    * - Variable
      - Units
      - Description
      - Source
    * - Current land cover
      - land-cover class labels 
      - Land-cover classification for most recent year, generated from multi-sensor satellite observations by the European Space Agency’s Copernicus Earth observation program and classified according to ESA’s Climate Change Initiative (CCI) land-cover categories.
      - ESA, 2017, Land Cover CCI Product User Guide, Version 2, maps.elie.ucl.ac.be/CCI/viewer/download/ESACCI-LC-Ph2-PUGv2_2.0.pdf
    * - Protected areas
      - binary (0 or 1)
      - Value of 1 indicates that a site is located in a protected area, while a value of 0 indicates it is not.
      - IUCN, World Database on Protected Areas, https://www.iucn.org/theme/protected-areas/our-work/world-database-protected-areas
    * - Population density
      - persons per km2 
      - Modeled distribution of human population for 2020, based on census data for the most disaggregated administrative units available.
      - CIESIN (Center for International Earth Science Information Network), 2018, Gridded Population of the World, Version 4 (GPWv4): Population Density, Revision 11, NASA Socioeconomic Data and Applications Center (SEDAC), https://doi.org/10.7927/H49C6VHW
    * - Declining population
      - binary (0 or 1)
      - Value of 1 indicates that human population in a 5 km buffer around a site declined during 2010 – 2020, while a value of 0 indicates it rose or did not change.
      - Developed by se.plan team, using 2.5 arc-minute data from: CIESIN (Center for International Earth Science Information Network), 2018, Gridded Population of the World, Version 4 (GPWv4): Population Density, Revision 11, NASA Socioeconomic Data and Applications Center (SEDAC), https://doi.org/10.7927/H49C6VHW
    * - Property rights protection
      - index (−2.5 to +2.5)
      - Downscaled version of the World Bank’s Rule of Law governance indicator, which is often interpreted as an indicator of property rights protection. Values range from −2.5 (very weak property rights) to +2.5 (very strong property rights). Varies by country and, when data are sufficient for downscaling, first-level administrative subdivision (e.g., state or province).
      - Developed by se.plan team, by downscaling national data from: World Bank, 2020, Worldwide Governance Indicators, https://info.worldbank.org/governance/wgi/
    * - Accessibility to cities
      - minutes
      - Travel time from a site to the nearest city in 2015.
      - D.J. Weiss, A. Nelson, H.S. Gibson, et al., 2018, A global map of travel time to cities to assess inequalities in accessibility in 2015, Nature,  doi:10.1038/nature25181; data downloaded from: https://malariaatlas.org/research-project/accessibility-to-cities/
