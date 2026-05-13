import { apiJson } from './client';

export async function listChannels() {
  return apiJson('/api/v1/channels');
}

export async function linkTelegramChannel(payload) {
  return apiJson('/api/v1/channels/telegram/link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function linkWhatsAppChannel(payload) {
  return apiJson('/api/v1/channels/whatsapp/link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function sendChannelTest(bindingId, payload) {
  return apiJson(`/api/v1/channels/${bindingId}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function listChannelApprovals() {
  return apiJson('/api/v1/channels/approvals');
}

export async function listChannelPairings(bindingId) {
  return apiJson(`/api/v1/channels/${bindingId}/pairings`);
}

export async function approveChannelSender(senderId, payload) {
  return apiJson(`/api/v1/channels/approvals/${senderId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
