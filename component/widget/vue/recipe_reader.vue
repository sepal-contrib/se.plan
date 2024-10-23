<template>
    <v-dialog v-model="dialog" max-width="900px">
      <v-card>
        <v-card-title>
          <v-icon color="white" class="mr-2">mdi-chef-hat</v-icon> Recipe: {{ recipe_name }}
        </v-card-title>
  
        <v-card-text ref="cardContent">

          <div ref="scrollableContent" style="max-height: 750px; overflow-y: auto;">
            <div v-if="data_dict">
            <!-- Display AOI -->
            <div>
              <strong>Area of Interest (AOI):</strong>
              <v-list dense>
                <v-list-item v-for="(aoi, type) in aoiDetails" :key="type">
                  <v-list-item-content>
                    <v-list-item-title>{{ type }}</v-list-item-title>
                    <v-list-item-subtitle>{{ aoi }}</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </div>
  
            <v-divider class="my-4"></v-divider>
  
            <!-- Display Benefits -->
            <v-card class="mb-4" flat>
              <v-card-title>
                <v-icon color="green darken-2" class="mr-2">mdi-leaf</v-icon>
                Benefits
              </v-card-title>
              <v-card-text>
                <v-simple-table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Theme</th>
                      <th>Asset</th>
                      <th>Priority</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(benefit, index) in filteredBenefits" :key="index">
                      <td>{{ benefit.name }}</td>
                      <td>{{ benefit.theme }}</td>
                      <td>{{ benefit.asset }}</td>
                      <td>
                        <v-chip :color="getPriorityChipColor(benefit.weight)" text-color="white">
                          {{ benefit.weight }}
                        </v-chip>
                      </td>
                    </tr>
                  </tbody>
                </v-simple-table>
              </v-card-text>
            </v-card>
  
            <v-divider class="my-4"></v-divider>
  
            <!-- Display Constraints -->
            <v-card class="mb-4" flat>
              <v-card-title>
                <v-icon color="red darken-2" class="mr-2">mdi-alert</v-icon>
                Constraints
              </v-card-title>
              <v-card-text>
                <v-simple-table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Asset</th>
                      <th>Unit</th>
                      <th>Masked values</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(constraint, index) in filteredConstraints" :key="index">
                      <td>{{ constraint.name }}</td>
                      <td>{{ constraint.asset }}</td>
                      <td>{{ constraint.unit }}</td>
                      <td>{{ constraint.value }}</td>
                    </tr>
                  </tbody>
                </v-simple-table>
              </v-card-text>
            </v-card>
  
            <v-divider class="my-4"></v-divider>
  
            <!-- Display Costs -->
            <v-card class="mb-4" flat>
              <v-card-title>
                <v-icon color="amber darken-2" class="mr-2">mdi-cash</v-icon>
                Costs
              </v-card-title>
              <v-card-text>
                <v-simple-table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Asset</th>
                      <th>Unit</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(cost, index) in filteredCosts" :key="index">
                      <td>{{ cost.name }}</td>
                      <td>{{ cost.asset }}</td>
                      <td>{{ cost.unit }}</td>
                    </tr>
                  </tbody>
                </v-simple-table>
              </v-card-text>
            </v-card>
  
            <v-divider class="my-4"></v-divider>
  
            <!-- Display Signature at the Bottom -->
            <div>
              <div class="center-content">
              <v-icon color="white" class="mr-2">mdi-fingerprint</v-icon>
              <strong>Recipe signature: </strong> {{ data_dict.signature }}
            </div>
            </div>
          </div>
  
          <div v-else>
            <v-alert type="info">No data available</v-alert>
          </div>
        </div>
        </v-card-text>
        <!-- Card Actions with Close Button -->
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="closeDialog" outlined=True>Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </template>

  
<script>
module.exports = {
    name: 'JsonDisplay',
    props: {
      data_dict: {
        type: Object,
        required: true,
      },
      value: {
        type: Boolean,
        default: true,
      },
      recipe_name: {
        type: String,
        default: 'Recipe',
      },
    },
    data() {
      return {
        dialog: this.value,
      };
    },
    watch: {
      dialog(newVal) {
    if (newVal) {
      this.$nextTick(() => {
        const scrollableContent = this.$refs.scrollableContent;
        if (scrollableContent) {
          scrollableContent.scrollTop = 0;
        }
      });
    }
  },

    },
    computed: {
      aoiDetails() {
        return {
          Primary:
            this.data_dict.aoi?.primary?.name ||
            this.data_dict.aoi?.primary?.asset_name ||
            'N/A',
          Custom: this.data_dict.aoi?.custom?.features
            ? `${this.data_dict.aoi.custom.features.length} features`
            : '0 features',
        };
      },
      filteredBenefits() {
        const benefits = this.data_dict.benefits;
        if (!benefits || !benefits.names) {
          return [];
        }
        return benefits.names
          .map((name, index) => ({
            name,
            theme: benefits.themes ? benefits.themes[index] : 'N/A',
            asset: benefits.assets ? benefits.assets[index] : 'N/A',
            weight: benefits.weights ? benefits.weights[index] : 0,
          }))
          .filter((benefit) => benefit.name);
      },
      filteredConstraints() {
        const constraints = this.data_dict.constraints;
        if (!constraints || !constraints.names) {
          return [];
        }
        return constraints.names
          .map((name, index) => ({
            name,
            asset: constraints.assets ? constraints.assets[index] : 'N/A',
            unit: constraints.units ? constraints.units[index] : 'N/A',
            value: (() => {
              const val = constraints.values ? constraints.values[index] : null;
              if (!val) {
                return 'N/A';
              }
              if (Array.isArray(val)) {
                if (val.length === 1) {
                  return val[0];
                } else if (val.length === 2) {
                  return `${val[0]} - ${val[1]}`;
                }
              }
              return val;
            })(),
          }))
          .filter((constraint) => constraint.name);
      },

      filteredCosts() {
        const costs = this.data_dict.costs;
        if (!costs || !costs.names) {
          return [];
        }
        return costs.names
          .map((name, index) => ({
            name,
            asset: costs.assets ? costs.assets[index] : 'N/A',
            unit: costs.units ? costs.units[index] : 'N/A',
          }))
          .filter((cost) => cost.name);
      },
    },
    methods: {
        getPriorityChipColor(weight) {
  const colors = [
    'grey lighten-1',    // Weight 0 - Neutral
    'green lighten-2',   // Weight 1 - Very Low Priority
    'lime lighten-2',    // Weight 2 - Low Priority
    'yellow lighten-2',  // Weight 3 - Medium Priority
    'orange lighten-2',  // Weight 4 - High Priority
    'red lighten-2',     // Weight 5 - Very High Priority
  ];
  const index = Math.min(Math.max(parseInt(weight), 0), colors.length - 1);
  return colors[index] || 'black';
},
      closeDialog() {
        this.dialog = false;
      },
    },
  };
  </script>
  
  <style scoped>
  .center-content {
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    font-size: 10px;
  }
  </style>
  