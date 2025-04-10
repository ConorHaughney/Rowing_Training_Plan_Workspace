import React, { useState, useEffect } from 'react';

const TrainingPlanApp = () => {
  const [trainingData, setTrainingData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetch('/api/training-data/')
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        setTrainingData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setError(error.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="loading">Loading training data...</div>;
  if (error) return <div className="error">Error loading data: {error}</div>;
  
  return (
    <div className="react-training-plan">
      <h2>Training Schedule (React)</h2>
      
      {trainingData.length === 0 ? (
        <p>No training data available</p>
      ) : (
        <table className="training-table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Date</th>
              <th>Morning Time</th>
              <th>Morning Session</th>
              <th>Afternoon Time</th>
              <th>Afternoon Session</th>
            </tr>
          </thead>
          <tbody>
            {trainingData.map(session => (
              <tr 
                key={`${session.date}-${session.id}`}
                className={session.date === currentDate ? 'today' : ''}
              >
                <td>{session.day}</td>
                <td>{new Date(session.date).toLocaleDateString()}</td>
                <td>{session.time_session_1}</td>
                <td>{session.session_1}</td>
                <td>{session.time_session_2}</td>
                <td>{session.session_2}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      
      <button onClick={() => window.location.reload()}>
        Refresh Training Data
      </button>
    </div>
  );
};

export default TrainingPlanApp;