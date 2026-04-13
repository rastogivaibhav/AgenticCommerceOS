import { apiJson } from './client';

export async function getOpsContext() {
  return apiJson('/api/v1/ops/context');
}

export async function getConnectorBindings() {
  return apiJson('/api/v1/connectors/bindings');
}

export async function getRuntimeProviders() {
  return apiJson('/api/v1/runtime/providers');
}
