<template>
  <div v-if="$options.aboutUrl" class="top-nav u-flex">
    <a :href="$options.aboutUrl">{{ $options.aboutText }}</a>
  </div>
</template>
<script>
  export default {
    name: 'Nav',
    aboutUrl: process.env.VUE_APP_ABOUT_URL,
    aboutText: process.env.VUE_APP_ABOUT_TEXT || 'About',
  };
</script>

<style lang="scss">
  .top-nav {
    border-bottom: 1px solid $gray-300;
    color: $white;
    flex-direction: row;
    justify-content: end;
    padding: 1em 0;
    width: 100%;
    z-index: 100;
    > * {
      margin-right: 2em;
    }
    a {
      color: $gray-700;
      text-decoration: none;
    }
  }
</style>
