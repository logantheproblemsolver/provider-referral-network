/**
 * This file is for the authentication middleware to make sure that this service can't be accessed without authentication
 */
import jwt from 'jsonwebtoken';
import { JwksClient } from 'jwks-rsa';
import { Request, Response, NextFunction } from 'express';

const JWKS_URL = process.env.RESOURCE_API_JWKS_URL;
if (!JWKS_URL) {
  throw new Error('RESOURCE_API_JWKS_URL is required');
}

const jwksClient = new JwksClient({
  jwksUri: JWKS_URL,
  cache: true,
  cacheMaxAge: 10 * 60 * 1000,
});

function getSigningKey(header: jwt.JwtHeader, callback: jwt.SigningKeyCallback): void {
  jwksClient.getSigningKey(header.kid, (err, key) => {
    if (err || !key) return callback(err ?? new Error('Signing key not found'));
    callback(null, key.getPublicKey());
  });
}

export function requireServiceAuth(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;
  if (!authHeader || typeof authHeader !== 'string' || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ error: 'Missing authorization header' });
    return;
  }
  const token = authHeader.slice(7);
  jwt.verify(
    token,
    getSigningKey,
    { issuer: 'resource-api', audience: 'verification-svc', algorithms: ['RS256'] },
    (err) => {
      if (err) {
        res.status(401).json({ error: 'Invalid or expired service token' });
        return;
      }
      next();
    }
  );
}
