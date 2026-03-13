<template>
  <!-- Main content row -->
  <tr :class="rowClass">
    <!-- Action buttons column -->
    <td class="pa-2 constraint-actions-col">
        <!-- Edit button -->
        <v-btn
          icon
          small
          :disabled="is_loading || has_error"
          @click="handleEdit"
          class="mr-1"
        >
          <v-icon small>mdi-pencil</v-icon>
        </v-btn>
        
        <!-- Map preview button -->
        <v-btn
          icon
          small
          :disabled="is_loading || has_error"
          @click="handleShowMap"
          class="mr-1"
        >
          <v-icon small>mdi-map</v-icon>
        </v-btn>
        
        <!-- Delete button (always enabled to allow cancellation) -->
        <v-btn
          icon
          small
          @click="handleDelete"
          class="mr-1 delete-btn"
          :class="{ 'delete-btn--loading': is_loading }"
        >
          <v-icon small>mdi-close</v-icon>
        </v-btn>
        
        <!-- Circular progress indicator -->
        <v-progress-circular
          v-if="is_loading"
          :indeterminate="true"
          color="primary"
          size="20"
          width="2"
          class="mr-1"
        ></v-progress-circular>
        
        <!-- Error icon -->
        <v-tooltip v-if="has_error" bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-icon
              small
              color="error"
              class="ml-1"
              v-bind="attrs"
              v-on="on"
            >
              mdi-alert-circle
            </v-icon>
          </template>
          <span>{{ error_message || "The data for this layer couldn't be retrieved. Please remove it or change the layer." }}</span>
        </v-tooltip>
    </td>
    
    <!-- Layer name column -->
    <td class="pa-2 constraint-name-col">
      <span class="text-body-2">{{ layer_name }}</span>
      <span v-if="layer_unit" class="text-caption text--secondary"> ({{ layer_unit }})</span>
    </td>
    
    <!-- Widget column -->
    <td class="pa-2 constraint-widget-col">
      <!-- Constraint widget (passed as component) -->
      <div v-if="constraint_widget && constraint_widget.length > 0" class="constraint-widget-container">
        <jupyter-widget :widget="constraint_widget[0]" />
      </div>
      <div v-else>
        <span class="text-caption text--disabled">No widget available</span>
      </div>
    </td>
  </tr></template>

<script>
export default {
  name: "ConstraintRow",
  
  props: {
    layer_id: {
      type: String,
      required: true
    },
    layer_name: {
      type: String,
      default: ""
    },
    layer_unit: {
      type: String,
      default: ""
    },
    is_loading: {
      type: Boolean,
      default: false
    },
    has_error: {
      type: Boolean,
      default: false
    },
    error_message: {
      type: String,
      default: ""
    },
    constraint_widget: {
      type: Array,
      default: () => []
    }
  },
  
  computed: {
    rowClass() {
      const classes = ["constraint-row"];
      if (this.is_loading) {
        classes.push("constraint-row--loading");
      }
      if (this.has_error) {
        classes.push("constraint-row--error");
      }
      return classes.join(" ");
    }
  },
  
  methods: {
    handleEdit() {
      if (!this.is_loading && !this.has_error) {
        this.on_edit(this.layer_id);
      }
    },
    
    handleShowMap() {
      if (!this.is_loading && !this.has_error) {
        this.on_show_map(this.layer_id);
      }
    },
    
    handleDelete() {
      this.on_delete(this.layer_id);
    }
  }
};
</script>

<style scoped>
.constraint-row {
  transition: background-color 0.3s ease;
}

/* Column sizing - proportional widths */
.constraint-actions-col {
  width: 15%; /* Actions column - compact but enough for 3 buttons + icons */
  min-width: 120px; /* Minimum to fit buttons */
}

.constraint-name-col {
  width: 30%; /* Name column - flexible, takes remaining space */
}

.constraint-widget-col {
  width: 55%; /* Widget column - 40% as requested */
}

/* Widget container fills the entire cell */
.constraint-widget-container {
  width: 100%;
}

/* Ensure buttons are properly aligned */
.constraint-row td {
  vertical-align: middle;
}

/* Loading state styling */
.constraint-row--loading .v-btn:not(.v-btn--disabled):not(.delete-btn) {
  opacity: 0.6;
}

/* Delete button special styling during loading */
.delete-btn--loading {
  background-color: rgba(0, 0, 0, 0.1) !important;
  border: 1px solid rgba(0, 0, 0, 0.3) !important;
}

.delete-btn--loading .v-icon {
  color: inherit !important;
}

/* Error state styling - keep normal text color, only show icon */
.constraint-row--error .text-body-2 {
  color: inherit; /* Keep normal text color */
}
</style>
