import React from 'react';
import ReactDOM from 'react-dom';
import TrainingPlanApp from './components/TrainingPlanApp';

document.addEventListener('DOMContentLoaded', () => {
  const reactRoot = document.getElementById('react-training-plan');
  if (reactRoot) {
    ReactDOM.render(<TrainingPlanApp />, reactRoot);
  }
});