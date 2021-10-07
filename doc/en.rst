se.plan
=======

Introduction
------------

Overview
^^^^^^^^

**se.plan** is a spatially explicit online tool designed to support forest restoration planning decisions by restoration stakeholders. It is part of `SEPAL <https://sepal.io/>`_ (System for Earth Observation Data Access, Processing and Analysis for Land Monitoring), a component of UN FAO’s free, open-source software suite, `Open Foris <http://www.openforis.org>`_. It aims to identify locations where the benefits of forest restoration are high relative to restoration costs, subject to biophysical and socioeconomic constraints that users impose to define the areas where restoration is allowable. The computation is performed using cloud-based supercomputing and geospatial datasets from Google Earth Engine available through SEPAL. As a decision-support tool, it is intended to be used in combination with other information users may have that provides greater detail on planning areas and features of those areas that **se.plan** might not adequately include. It offers users the option to replace its built-in data layers, which are based on publicly available global datasets, with users’ own customized layers. Please see :ref:`Appendix A` for a list of **se.plan**’s built-in data layers and their sources.

The sections below highlight key features of **se.plan**. A high-level view of using the tool can be described as follows: 

.. rst-class:: center

    Users start by (i) selecting their geographical planning area, (ii) rating the relative importance of different restoration benefits from their perspective, and (iii) imposing constraints that limit restoration to only those sites they view as suitable, in view of ecological and socioeconomic risks. **se.plan** then generates maps and related information on restoration’s benefits, costs, and risks for all suitable sites within the planning area. 

In addition to reading this manual, we encourage users to watch **se.plan** YouTube videos: `video being shot`_.

Geographical resolution and scope
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**se.plan** divides the Earth’s surface into grid cells with 30 arc-second resolution (≈1km at the equator). It includes only grid cells that satisfy the following four criteria:

-   They are in countries or territories of Africa and the Near East, Asia and the Pacific, and Latin America and the Caribbean that the World Bank classified as *low or middle-income countries* or territories (LMICs) during most years during 2000–2020. These countries and territories number 139 and are listed in :ref:`Appendix B`.
-   They include areas where tree cover can potentially occur under current climatic conditions, as determined by `Bastin et al. (2019) <https://doi.org/10.1126/science.aax0848>`_.
-   Their current tree cover, as measured by the European Space Agency’s Copernicus Programme (`Buchhorn et al. 2020 <https://doi.org/10.3390/rs12061044>`_), is less than their potential tree cover.
-   They are not in urban use.

**se.plan** labels grid cells that satisfy these criteria potential restoration sites. It treats each grid cell as an independent restoration planning unit, with its own potential to provide restoration benefits and to entail restoration costs and risks.

Methodology
-----------

Selection of planning area
^^^^^^^^^^^^^^^^^^^^^^^^^^

**se.plan** offers users multiple ways to select their planning area, which **se.plan** labels as *Area Of Interest* (AOI) as described in the :ref:`Usage section`. 

Restoration indicators
^^^^^^^^^^^^^^^^^^^^^^

Restoration offers many potential benefits. In its current form, **se.plan** provides information on four benefit categories:

-   Biodiversity conservation
-   Carbon sequestration
-   Local livelihoods
-   Wood production

**se.plan** includes two indicators each for biodiversity conservation and local livelihoods and one indicator each for carbon sequestration and wood production. Each indicator is associated with a data layer that estimates each grid cell’s relative potential to provide each benefit if the grid cell is restored;  the relative potential is measured on a scale of 1 (low) to 5 (high). Please see :ref:`Appendix C` for more detail on the interpretation and generation of the data layers for the benefit indicators.

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

Please see :ref:`Appendix F` for more detail on the interpretation and generation of the data layers for the constraints.

Customization
^^^^^^^^^^^^^

Every Constraints and benefits are based on layers provided within the tools. These layer may not be covering the AOI selected by the user or provide less accurate/updated data than the National datasets available. To allow user to improve the quality of the analysis **se.plan** provides the possiblity of replacing these datasets by any layer available with Google Earth Engine.

Please see :ref:`Usage` for more details on the customization process.

Output
^^^^^^

The output provides two outputs: 

- A map of the Restoration suitability index scaled from 1 (low suitability) to 5 (high suitability). This map, generated within the Google Earth Engine API can be displayed in the app but also exported as a GEE asset or a .tif file in your SEPAL folders. 

- A dashboard that summarize informations on the AOI and sub-AOIs defined by the users. The suitability index is thus presented as surfaces in Mha but **se.plan** also displays the mean values of the benefits and the sum of all the used constraints and cost over the AOIs.

.. Appendix C:

Benefits data layers
--------------------

In its current form, **se.plan** provides information on four categories of potential benefits of forest restoration:

- Biodiversity conservation
- Carbon sequestration
- Local livelihoods
- Wood production

**se.plan** does not predict the levels of benefits that will occur if forests are restored. Instead, it uses data on benefit-related site characteristics to quantify the potential of a site to provide benefits if it is restored. To clarify this distinction, consider the case of species extinctions. A predictive tool might, for example, estimate the number of extinctions avoided if restoration occurs. To do so, it would need to account for restoration scale and interdependencies across sites associated with distances and corridors between restored sites. **se.plan** instead takes a simpler approach: it includes information on the total number of critically endangered and endangered amphibians, reptiles, birds, and mammals at each site. Sites with a larger number of critically endangered and endangered species are ones where the potential number of avoided extinctions is greater. Realizing the benefit of reduced extinctions depends on factors beyond simply restoring an individual site, including the type of forest that is restored (native tree species or introduced tree species, single tree species or multiple tree species, etc.) and the pattern of restoration in the rest of the landscape. Interpreting se.plan output in the context of additional, location-specific information available to a user is therefore important.

Quantitative measures of potential benefits in se.plan should be viewed as averages for a grid cell. Potential benefits could be higher at some locations within a given grid cell and lower at others.

.. list-table::
    :header-rows: 1
    
    * - Variable
      - category
      - Units
      - Description
      - Source
    * - Endangered species
      - Biodiversity conservation
      - count
      - Total number of critically endangered and endangered amphibians, reptiles, birds, and mammals whose ranges overlap a site. Rationale for including in se.plan: sites with a larger number of critically endangered and endangered species are ones where successful forest restoration can potentially contribute to reducing a larger number of extinctions.
      - World Bank, which processed over 25,000 species range maps from: (i) IUCN, The IUCN Red List of Threatened Species, https://www.iucnredlist.org; and (ii) BirdLife International, Data Zone, http://datazone.birdlife.org/species/requestdis. Resolution of World Bank layer: 1 kilometer. More information may be found at https://datacatalog.worldbank.org/dataset/terrestrial-biodiversity-indicators, and data may be downloaded at http://wbg-terre-biodiv.s3.amazonaws.com/listing.html. See also: (i) Dasgupta, Susmita; Wheeler, David. 2016. Minimizing Ecological Damage from Road Improvement in Tropical Forests. Policy Research Working Paper: No. 7826. World Bank, Washington, DC. (ii) Danyo Stephen, Susmita Dasgupta and David Wheeler. 2018. Potential Forest Loss and Biodiversity Risks from Road Improvement in Lao PDR. World Bank Policy Research Working Paper 8569. World Bank, Washington, DC. (iii) Damania Richard, Jason Russ, David Wheeler and Alvaro Federico Barra. 2018. The Road to Growth: Measuring the Tradeoffs between Economic Growth and Ecological Destruction, World Development, Elsevier, vol. 101(C), pp. 351-376.
    * - BII gap
      - Biodiversity conservation
      - percent
      - The biodiversity intactness index (BII) describes the average abundance of a large and diverse set of organisms in a given geographical area, relative to the set of originally present species. se.plan subtracts the BII from 100, to measure the gap between full intactness and current intactness. Rationale for including in se.plan: sites with a larger BII gap are ones where successful forest restoration can potentially contribute to reducing a larger gap.
      - T. Newbold, L. Hudson, A. Arnell, et al., 2016, Dataset: Global map of the Biodiversity Intactness Index, from Newbold et al., 2016, Science, Natural History Museum Data Portal (data.nhm.ac.uk), https://doi.org/10.5519/0009936. Resolution of Newbold et al. layer: 1 km. See also: (i) Scholes, R.J. and Biggs, R., 2005. A biodiversity intactness index. Nature, 434(7029), pp.45-49. (ii) Newbold, T., Hudson, L.N., Arnell, A.P., Contu, S., De Palma, A., Ferrier, S., Hill, S.L., Hoskins, A.J., Lysenko, I., Phillips, H.R. and Burton, V.J., 2016. Has land use pushed terrestrial biodiversity beyond the planetary boundary? A global assessment. Science, 353(6296), pp.288-291.
    * - Aboveground carbon accumulation
      - Carbon sequestration
      - metric tons of carbon per hectare per year
      - Projected potential mean annual aboveground carbon accumulation rates for natural forest regeneration during 2020-2050. Accounts for variation in such factors as climate and soil. Rationale for including in se.plan: climate mitigation benefits of forest restoration are greater where forests regenerate more rapidly. Although the layer refers to natural regeneration, it might also reflect relative spatial differences in aboveground carbon sequestration in planted forests, given that climate and soil also affect growth of those forests. Can also be viewed as complementing the plantation growth rate layer (see below).
      - S.C. Cook-Patton, S.M. Leavitt, D. Gibbs, et al., 2020, Mapping carbon accumulation potential from global natural forest regrowth, Nature 585(7826), pp. 545–550, https://doi.org/10.1038/s41586-020-2686-x. Resolution of Cook-Patton et al. layer: 1 km.
    * - Forest employment
      - Local livelihoods
      - count
      - Number of forest-related jobs per ha of forest in 2015, summed across three economic activities: forestry, logging, and related service activities; manufacture of wood and of products of wood and cork, except furniture; and manufacture of paper and paper products. Varies by country and, when data are sufficient for downscaling, first-level administrative subdivision (e.g., state or province). Rationale for including in se.plan: a higher level of forest employment implies the existence of attractive business conditions for labor-intensive wood harvesting and processing industries, which tends to make forest restoration more feasible when income for local households is a desired benefit.
      - Developed by se.plan team, by downscaling national data from: International Labour Organization, 2020, Employment by sex and economic activity - ISIC level 2 (thousands) | Annual, ILOSTAT database, https://ilostat.ilo.org/data
    * - Woodfuel harvest
      - Local livelihoods
      - cubic meters per hectare
      - Harvest of wood fuel per hectare of forest in 2015. Rationale for including in se.plan: a higher level of wood fuel harvest implies greater demand for wood fuel as an energy source, which tends to make forest restoration more feasible when supply of wood to meet local demands is a desired benefit.
      - Developed by se.plan team, by downscaling national data from: UN FAO, 2020, Forestry Production and Trade, FAOSTAT, http://www.fao.org/faostat/en/#data/FO
    * - Plantation growth rate
      - Wood production
      - dry metric tons of woody biomass per hectare per year
      - Potential annual production of woody biomass by fast-growing trees such as eucalypts, poplars, and willows. Rationale for including in se.plan: faster growth of plantation trees tends to make forest restoration more feasible when desired benefits include income for landholders and wood supply to meet local and export demands.
      - F. Albanito, T. Beringer, R. Corstanje, et al., 2016, Carbon implications of converting cropland to bioenergy crops or forest for climate mitigation: a global assessment, GCB Bioenergy 8, pp. 81–95, https://doi.org/10.1111/gcbb.12242. Resolution of Albanito et al. layer: 55 km.

.. Appendix D:

benefit-cost ratio
------------------

In its current form, **se.plan** includes numerical estimates of four categories of potential restoration benefits for each potential restoration site:

-   Biodiversity conservation
-   Carbon sequestration
-   Local livelihoods
-   Wood production.

Denote these benefits, respectively, by $$B_1$$, $$B_2$$, $$B_3$$, and $$B_4$$. The data on which the benefit estimates are based have different units. To enable the benefit estimates to be compared to each other, **se.plan** converts them to the same, relative scale, which ranges from 1 (low) to 5 (high). **se.plan** includes two indicators each for $$B_1$$ and $$B_3$$ and a single indicator for $$B_2$$ and $$B_4$$. We return to this difference in number of indicators below.

**se.plan** users rate the relative importance of each benefit on a scale of 1 (low) to 5 (high). **se.plan** treats these ratings as weights and calculates a restoration value index for each site by the weighted-average formula:

.. math::

    Restoration value index = (w_1B_1 + w_2B_2 + w_3B_3 + w_4B_4.) / (w_1 + w_2 + w_3 + w_4)
    
Where $$w_1$$, $$w_2$$, $$w_3$$, and $$w_4$$ are the user ratings for the four corresponding benefits.

**se.plan** also includes numerical estimates of restoration cost, defined as the sum of opportunity cost and implementation cost in 2017 US dollars per hectare, for each potential restoration site. **se.plan** calculates an approximate benefit-cost ratio by dividing the restoration value index by the estimate of restoration cost:

.. math::

	Benefit-cost ratio = Restoration value index / Restoration cost.
    
The benefit-cost ratio in **se.plan** is approximate in several ways. In particular, **se.plan** does not value potential restoration benefits in monetary terms, and it does not calculate the discounted sum of benefits over a multi-year time period that extends into the future. Its cost estimates account for the future to a greater degree, however; see :ref:`Appendix E`. As a final step, se.plan converts the benefit-cost ratio across all sites in the user’s area of interest to a scale from 1 (low) to 5 (high). It reports this value as the restoration suitability index on the map and dashboard.

As noted above, **se.plan** includes two indicators for benefits $$B_1$$ (biodiversity conservation) and $$B_3$$ (local livelihoods). For $$B_1$$, the two indicators are the *biodiversity intactness index* and *number of endangered species*. Denote these two indicators by $$B_1a$$ and $$B_1b. **se.plan** converts each of these indicators to a 1-5 scale and then calculates the overall biodiversity benefit, $$B_1$$, as their simple average:

.. math::

	B_1 = (B_1a + B_1b) / 2
    
**se.plan** calculates the overall local livelihoods benefit in the same way from its two constituent indicators, *forest employment* and *woodfuel harvest*.

.. Appendix E:

Cost data layers
----------------

In the cases of benefits (:ref:`Appendix C`) and constraints (:ref:`Appendix F`), the **se.plan** team adopted the tool’s data layers primarily from existing sources, with little or no modification of the original layers. In contrast, it developed wholly new data layers for both the *opportunity cost* and the *implementation cost* of forest restoration. Developing these layers involved multiple steps, which are described below.

Opportunity cost
^^^^^^^^^^^^^^^^

*pportunity cost* in **se.plan** refers to the value of land if it is not restored to forest: i.e., the value of land in its current use. A higher opportunity cost tends to make restoration less feasible, although restoration can nevertheless be feasible on land with a high opportunity cost if it generates sufficiently large benefits. se.plan assumes that the alternative land use would be some form of agriculture, either cropland or pastureland. It sets the *opportunity cost* of potential restoration sites equal to the value of cropland for all sites where crops can be grown, with the opportunity cost for any remaining sites set equal to the value of pastureland. 

The value of land in agricultural use is defined as the portion of agricultural profit that is attributable to land as a production input. Economists label this portion “land rent”. Agricultural profit is the difference between the gross revenue a farmer receives from selling agricultural products (= product price × quantity sold) and the expenditures the farmer makes on variable inputs, such as seeds and fertilizer, used in production. It is the return earned by fixed inputs, which include labor and capital (e.g., equipment, structures) in addition to land. These relationships imply that the **se.plan** team needed to sequentially estimate gross revenue, profit, and land rent. 

The team assumed that forest restoration is intended to be permanent, and so it estimated land rent in perpetuity: the opportunity cost of forgoing agricultural use of a restored site forever, not just for a single year. The estimates of this long-run opportunity cost in **se.plan** are expressed in US dollars per hectare for reference year 2017. 

Cropland
********

The workflow to develop cropland opportunity cost can be summarized as follows:

#.  The se.plan team obtained gridded data on 2010 value of crop production per hectare (i.e., gross revenue per hectare) from the International Food Policy Research Institute’s MapSPAM project (International Food Policy Research Institute, 2019; Yu et al., 2020). The resolution of this layer was 5 arc-minutes (~10 km at the equator).
#.  The team updated the MapSPAM data to 2017 using  country-specific data on total cereal yield from FAOSTAT (UN FAO, 2020a) and the global producer price index for total cereals, also from FAOSTAT. The MapSPAM data reflect gross revenue from a much wider range of crops than cereals, but cereals are the dominant crops in most countries. 
#.  The team multiplied the data from step 2 by an estimate of the share of crop revenue that was attributable to land, i.e., the land-rent share. The rent-share estimates differed across countries and, where data permitted, by first-level administrative subdivisions (e.g., states, provinces) within countries. The team developed the rent-share estimates through a two-step procedure:
    
    #.  It used 229,859 annual survey observations spanning 2004–2017 from 196,327 unique farm households (UN FAO, 2020c) in 32 low- and middle-income countries (LMICs) to statistically estimate a model that related profit from growing crops to fixed inputs. Table E1 shows the distribution of observations by country in the statistical model, and Table E2 shows the estimation results for the model. The dependent variable in the model was the natural logarithm of profit (lnQuasiRent in the table), and fixed inputs were represented by the natural logarithms of cultivated area (lncultivated) and family labor (lnfamlabor) and a binary (“dummy”) variable that indicated whether the farm was mechanized (dmechuse). The model also included year dummies and fixed effects for regions (countries or first-level subdivisions, depending on the survey), which controlled for unobserved factors that varied across time but not regions (the year dummies) and unobserved factors that varied across regions but not time (the region fixed effects). Post-estimation, the team calculated land rent for each observation by multiplying profit by 0.325, the estimated coefficient on the log cultivated area variable. This procedure assumes that the coefficients on inputs in the log-log profit model can be interpreted as profit shares. This assumption is valid if production has constant returns to scale: i.e., if the coefficients sum to 1, which they approximately do in the model. 
    #.  The team used sampling weights from the surveys to calculate mean values of crop revenue and land rent for each region in the sample. It then calculated the ratio of mean land rent to mean crop revenue—i.e., the land-rent share—for each region, and it statistically related the rent shares to a set of spatial variables, which included the region’s gross domestic product per capita in 2015 (Kummu et al., 2018), its population density in 2015 (CIESIN, 2018), the strength of property rights in it (see discussion of this variable in Appendix F), area shares of terrestrial ecoregions in it (Olson and Dinerstein, 2002), and its classification by World Bank region. Table E3 shows the estimation results for the rent-share model. The team used this model to predict rent shares for the LMICs spanned by se.plan and, where possible, first-level subdivisions within them.

#. The team estimated the value of cropland in perpetuity by dividing the annual land rent estimates from step 3 by 0.07, under the assumption that the financial discount rate is 7%. It based this assumption on the mean value of real interest rates across the LMICs in the tool (World Bank, 2020).

Pastureland
***********

The se.plan team used similar procedures to estimate the value of pastureland. In place of cropland steps 1 and 2, it:

#.  Predicted pastureland area in 2015 by first statistically relating pastureland percentage in 2000 (UN FAO, 2007, van Velthuizen et al., 2007) to a set of land-cover variables for 2000 at 300m resolution from the European Space Agency (ESA, 2017), and then using the resulting statistical model and 2015 values of the land-cover variables to predict 2015 pastureland area within each 300m grid cell.
#.  Calculated gross revenue from livestock in ~2017 by multiplying gridded data on livestock numbers (buffaloes, cattle, goats, horses, sheep) in 2010 at 10km resolution (UN FAO, 2018) by 2017 estimates of production value per animal, calculated by using country-specific data on stocks of animals and production value of livestock products from FAOSTAT (UN FAO, 2020b). It adjusted the resulting estimates of gross revenue per grid cell to include production only from grazing lands, not from feedlots, by using FAO estimates of national shares of meat production from grazing lands provided by the World Bank.
#.  Calculated gross revenue per hectare in ~2017 by dividing gross revenue from step b by pastureland area from step a. 

Compared to cropland step 3, household survey data on livestock production on pastureland (FAO, 2020c) were too limited to estimate land-rent shares that varied across countries or first-level subdivisions. Instead, the statistical rent-share estimate used in the tool, 6.1% of gross revenue, is identical across all countries and first-level subdivisions.

Step 4 was the same as for cropland.

Implementation costs
^^^^^^^^^^^^^^^^^^^^

Implementation costs refer to the expense of activities required to regenerate forests. They include both: (i) initial expenses incurred in the first year of restoration (establishment costs), which are associated with such activities as site preparation, planting, and fencing; and (ii) expenses associated with monitoring, protection, and other activities in years following establishment (operating costs), which are required to enable the regenerated stand to reach the “free to grow” stage. se.plan does not report these two components of implementation costs separately. Instead, it reports the aggregate cost of restoring a site, in 2017 US dollars per hectare, by summing the estimates of opportunity cost and implementation costs. This aggregate cost is the cost variable that it includes in the benefit-cost ratio (Appendix D). The estimates of implementation costs vary by country and, for countries with sufficient data, by first-level subdivision.

As discussed above, se.plan assumes that current land use is some form of agriculture. It therefore also assumes that regeneration requires planting, as sources of propagules for natural regeneration are often not adequate on land that has been cleared for agriculture. se.plan does not ignore natural regeneration as a restoration option, however, as it includes a constraint layer that predicts the variability of natural regeneration success (see :ref:`Appendix E`).

The se.plan team estimated implementation costs in three steps:

#.  It extracted data on implementation costs from project appraisal reports and implementation completion reports for 50 World Bank afforestation and reforestation projects spanning 24 LMICs during the past 2-3 decades. Afforestation refers to regeneration of sites where the most recent land use was not forest, e.g., agriculture, while reforestation refers to regeneration of sites that only recently lost their forest cover, e.g., due to harvesting or wildfire. Whenever possible, the team extracted data on operating costs in addition to data on establishment costs, with operating costs typically extending up to 3–5 years after establishment (depending on project and site). It converted all estimates to a per-hectare basis, expressed in constant 2011 US dollars. It classified the estimates by country and, where possible, first-level subdivision. 

#.  It statistically related the natural logarithm of implementation cost per hectare to a set of variables hypothesized to explain it, including: (i) GDP per capita, also natural log transformed (Kummu et al., 2018); (ii) a dummy variable distinguishing reforestation from afforestation (regeneration of sites where the most recent land use was not forest, e.g., agriculture); (iii) a dummy variable distinguishing natural regeneration from planting; (iv) the total regenerated area (natural log transformed); (v) dummy variables giving the dominant biome in the region (tropical or subtropical, vs. temperate/boreal; (UN FAO, 2013); (vi) a dummy variable indicating whether the project began pre- or post-2010; (vii) a dummy variable that can be interpreted as indicating whether the cost estimate accounted for project overhead costs or not (“UnitArea”); and (viii) a set of dummy variables that indicated projects that included special types of regeneration that did not commonly occur in the dataset, which mainly referred to regeneration of small to large stands of trees on interior sites. Table E4 shows estimation results for the model.

#.  The team predicted spatial estimates of implementation costs by region (country or first-level subdivision) by inserting into the model gridded GDP estimates for 2011, the mean of project area in the estimation sample, and the biome variables. All of the other binary variables were set to 0. As a final step, the team converted the predicted implementation costs to constant 2017 US dollars using annual inflation rates between 2012 and 2017. 


References
^^^^^^^^^^

-   CIESIN (Center for International Earth Science Information Network). 2018. Gridded Population of the World, Version 4 (GPWv4): Population Density, Revision 11. NASA Socioeconomic Data and Applications Center (SEDAC). https://doi.org/10.7927/H49C6VHW. 
-   ESA. 2017. Land Cover CCI Product User Guide, Version2. maps.elie.ucl.ac.be/CCI/viewer/download/ESACCI-LC-Ph2-PUGv2_2.0.pdf. 
-   International Food Policy Research Institute. 2019. Global Spatially-Disaggregated Crop Production Statistics Data for 2010 Version 2.0. https://doi.org/10.7910/DVN/PRFF8V, Harvard Dataverse, V4.
-   Kummu, M., Taka, M. & Guillaume, J. 2018. Gridded global datasets for Gross Domestic Product and Human Development Index over 1990–2015. Sci Data 5, 180004. https://doi.org/10.1038/sdata.2018.4. 
-   Olson, D. M., and E. Dinerstein. 2002. The Global 200: Priority ecoregions for global conservation. Annals of the Missouri Botanical Garden 89:125-126. https://geospatial.tnc.org/datasets/7b7fb9d945544d41b3e7a91494c42930_0.
-   van Velthuizen, H., Huddleston, B., Fischer, G., Salvatore, M., Ataman, E., et al. 2007. Mapping biophysical factors that influence agricultural production and rural vulnerability. Environment and Natural Resources Series No. 11. FAO, Rome.
-   Yu, Q., You, L., Wood-Sichra, U., Ru, Y., Joglekar, A. K. B., et al. 2020 (in review). A cultivated planet in 2010: 2. the global gridded agricultural production maps. Earth Syst. Sci. Data Discuss. https://doi.org/10.5194/essd-2020-11.
-   UN FAO. 2007. Occurrence of Pasture and Browse (FGGD). https://data.apps.fao.org/map/catalog/srv/eng/catalog.search#/metadata/913e79a0-7591-11db-b9b2-000d939bc5d8. 
-   UN FAO. 2013. Global Ecological Zones (second edition). https://data.apps.fao.org/map/catalog/srv/eng/catalog.search#/metadata/2fb209d0-fd34-4e5e-a3d8-a13c241eb61b. 
-   UN FAO. 2018. Gridded Livestock of the World – Latest – 2010 (GLW 3). https://dataverse.harvard.edu/dataverse/glw_3, Harvard Dataverse, V3. 
-   UN FAO. 2020a. FAOSTAT: Crops. http://www.fao.org/faostat/en/#data/QC.
-   UN FAO. 2020b. FAOSTAT: Livestock Primary. http://www.fao.org/faostat/en/#data/QL.
-   UN FAO. 2020c. RuLIS - Rural Livelihoods Information System. http://www.fao.org/in-action/rural-livelihoods-dataset-rulis/en/.
-   World Bank. 2020. World Development Indicators. https://databank.worldbank.org/source/world-development-indicators. 
-   World Bank. Various years. Projects & Operations. Project appraisal documents and implementation completion reports for selected projects. https://projects.worldbank.org/en/projects-operations/projects-home. 


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
