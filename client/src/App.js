import React from "react";

import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";

const { REACT_APP_HOST, REACT_APP_PORT, REACT_APP_PROTOCOL } = process.env;

const App = () => (
  <SwaggerUI
    url={`${REACT_APP_PROTOCOL}://${REACT_APP_HOST}:${REACT_APP_PORT}/static/spec.yaml`}
  />
);

export default App;
