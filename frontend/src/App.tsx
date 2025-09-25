import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Sales from './pages/Sales';
import Products from './pages/Products';
import Warehouses from './pages/Warehouses';
import { AuthProvider } from './contexts/AuthContext';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Switch>
          <Route path="/" exact component={Dashboard} />
          <Route path="/sales" component={Sales} />
          <Route path="/products" component={Products} />
          <Route path="/warehouses" component={Warehouses} />
        </Switch>
      </Router>
    </AuthProvider>
  );
};

export default App;