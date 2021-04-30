import ReaderView from '@/views/ReaderView.vue';

export default [
  { path: '/', redirect: 'reader' },
  { path: '/reader/:urn?', component: ReaderView, name: 'reader' },
];
