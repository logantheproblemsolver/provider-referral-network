/**
 * This file is the index file to start the server. I know this can be set up in multiple ways, some people do an app file to create routes and then a server file to start the server. For this take home test I wanted to keep it simple and have it all in one file
 */
import express from 'express';
import { requireServiceAuth } from './middleware/auth';

const app = express();
const PORT = process.env.PORT || process.env.VERIFICATION_SVC_PORT || 9000;

// This is just a healthcheck endpoint
app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

/** This API is a GET request that requires authentication and verifies if an npi is a valid npi. Right now it just checks if the NPI is ten digits, but in production this would use check against a real registry like: npiregistry.cms.hhs.gov/search */
app.get('/verify/:npi', requireServiceAuth, (req, res) => {
  const npi = Array.isArray(req.params.npi) ? req.params.npi[0] : req.params.npi; // Express 5 types req.params as string | string[]
  if (!/^\d{10}$/.test(npi)) {
    res.status(422).json({ valid: false, npi, reason: 'NPI must be exactly 10 digits' });
    return;
  }
  res.json({ valid: true, npi });
});

app.listen(PORT, () => {
  console.log(`verification-svc listening on port ${PORT}`);
});
