<template>
  <v-dialog v-model="show" max-width="800" persistent>
    <v-card>
      <v-card-title class="text-h5">
        <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
        Invalid Data Detected
      </v-card-title>

      <v-card-text>
        <p class="mb-4">
          The following data issues were found and the invalid items have been
          automatically removed from the loaded recipe. The recipe will work with
          the remaining valid data.
        </p>

        <v-expansion-panels multiple v-model="expanded">
          <v-expansion-panel v-if="benefits && benefits.length">
            <v-expansion-panel-header>
              <span class="font-weight-bold">Benefits ({{ benefits.length }} issues)</span>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <div v-for="(err, i) in benefits" :key="`b-${i}`" class="mb-3 pa-3 rounded error-item">
                <div class="font-weight-bold text-body-1">• {{ err.name || 'Unknown' }}</div>
                <div class="ml-4 text-body-2">
                  Type: {{ err.data_type || 'unknown' }}, Values: {{ err.values }}
                  <br />
                  <span class="error--text">Error: {{ err.error || 'Unknown error' }}</span>
                </div>
              </div>
            </v-expansion-panel-content>
          </v-expansion-panel>

          <v-expansion-panel v-if="constraints && constraints.length">
            <v-expansion-panel-header>
              <span class="font-weight-bold">Constraints ({{ constraints.length }} issues)</span>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <div v-for="(err, i) in constraints" :key="`c-${i}`" class="mb-3 pa-3 rounded error-item">
                <div class="font-weight-bold text-body-1">• {{ err.name || 'Unknown' }}</div>
                <div class="ml-4 text-body-2">
                  Type: {{ err.data_type || 'unknown' }}, Values: {{ err.values }}
                  <br />
                  <span class="error--text">Error: {{ err.error || 'Unknown error' }}</span>
                </div>
              </div>
            </v-expansion-panel-content>
          </v-expansion-panel>

          <v-expansion-panel v-if="costs && costs.length">
            <v-expansion-panel-header>
              <span class="font-weight-bold">Costs ({{ costs.length }} issues)</span>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <div v-for="(err, i) in costs" :key="`co-${i}`" class="mb-3 pa-3 rounded error-item">
                <div class="font-weight-bold text-body-1">• {{ err.name || 'Unknown' }}</div>
                <div class="ml-4 text-body-2">
                  Type: {{ err.data_type || 'unknown' }}, Values: {{ err.values }}
                  <br />
                  <span class="error--text">Error: {{ err.error || 'Unknown error' }}</span>
                </div>
              </div>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-tooltip top>
          <template v-slot:activator="{ on, attrs }">
            <v-btn 
              outlined 
              color="error" 
              class="ma-2" 
              @click="on_cancel"
              v-bind="attrs"
              v-on="on"
            >
              Cancel
            </v-btn>
          </template>
          <span>Abort the recipe load and reset to default values</span>
        </v-tooltip>
        
        <v-tooltip top>
          <template v-slot:activator="{ on, attrs }">
            <v-btn 
              outlined 
              color="primary" 
              class="ma-2" 
              @click="on_continue"
              v-bind="attrs"
              v-on="on"
            >
              Continue
            </v-btn>
          </template>
          <span>Work with the cleaned data (you can save the recipe later if desired)</span>
        </v-tooltip>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'InvalidDataDialog',
  props: {
    show: { type: Boolean, default: false },
    benefits: { type: Array, default: () => [] },
    constraints: { type: Array, default: () => [] },
    costs: { type: Array, default: () => [] },
  },
  data() {
    return {
      // indices of expanded panels; will be set based on which sections have errors
      expanded: [],
    }
  },
  mounted() {
    this.updateExpanded()
  },
  watch: {
    show(newVal) {
      if (newVal) {
        // When dialog opens, expand all panels
        this.updateExpanded()
      }
    },
    benefits(newVal) {
      this.updateExpanded()
    },
    constraints(newVal) {
      this.updateExpanded()
    },
    costs(newVal) {
      this.updateExpanded()
    },
  },
  methods: {
    updateExpanded() {
      // Expand all panels that have errors
      const idx = []
      let i = 0
      if (this.benefits && this.benefits.length) {
        idx.push(i)
      }
      i += 1
      if (this.constraints && this.constraints.length) {
        idx.push(i)
      }
      i += 1
      if (this.costs && this.costs.length) {
        idx.push(i)
      }
      this.expanded = idx
    },
  },
}
</script>

<style scoped>
/* Theme-aware error item background */
.error-item {
  background-color: rgba(0, 0, 0, 0.05);
}

.theme--dark .error-item {
  background-color: rgba(255, 255, 255, 0.05);
}
</style>
