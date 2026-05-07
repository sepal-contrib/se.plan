<!-- Custom dialog to trigger a resize event when it is open -->
<template>
    <v-dialog v-model="show" :persistent="persistent" :max-width="max_width" :min-width="min_width" :retain-focus="retain_focus">
          <jupyter-widget v-for="(child, index) in children" :key="index" :widget="child"></jupyter-widget>
    </v-dialog>
  </template>
  
  <script>
  export default {
    watch: {
      show(newValue) {
        if (newValue) {
          console.log('Dialog is shown!!!');
          window.dispatchEvent(new Event("resize"));
        }
      }
    }
  };
  </script>