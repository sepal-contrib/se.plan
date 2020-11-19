################################
##      constraints tile      ##
################################
CONSTRAINT_TXT = """ 
        Select constraints from the dropdown menu below to add a limitation to consider.  
        For each constraint, choose values greater than or less than a particular value.  
        Note that some constraint are scaled differntly so please read their short description after selection to assign appropriate values.
        """
CRITERIA_LABEL = "Criteria"

##############################
##      potential tile      ##
##############################
POTENTIAL_TXT = """Max % tree cover in land use classes"""
LAND_USE_SELECT_LABEL = "Which land uses allow restoration?"
MAX_ALLOW_TREECOVER_LABEL = 'Maximum allowable percent tree cover in {}:'


##########################
##      Goals tile      ##
##########################
GOAL_SELECT_LABEL = 'restoration goals'

############################
##      Custom layer      ##
############################
DEFAULT_TABLE_LABEL = 'Weighted default layers'
CUSTOM_TABLE_LABEL = 'Use customized layers'
BTN_USE_QUESTIONNAIRE = 'Apply questionnaire answers'
BTN_USE_DEFAULT = 'Apply default parameters'
CUSTOMIZE_TILE_TXT = """  
    by clicking on the 'apply questionnaire button, the different layers will be wheighted to best meet your answers. The User still have liberty of changing the value of any weight. In the second Panel The user will find all the layer that can be changed with custom one.    
    > Be extra careful wile changing the wheigth and using custom layer as it can lead to wrong or inacurate recommandations
    """