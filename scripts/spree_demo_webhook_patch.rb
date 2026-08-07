# frozen_string_literal: true

def acos_allow_private_webhooks?
  ENV.fetch('ACOS_ALLOW_PRIVATE_WEBHOOKS', '').strip.downcase.in?(%w[1 true yes on])
end

if acos_allow_private_webhooks?
  module AcosDemoWebhookDeliveryPatch
    private

    def make_request
      return super unless acos_allow_private_webhooks?

      headers = {
        'Content-Type' => 'application/json',
        'User-Agent' => 'Spree-Webhooks/1.0',
        'X-Spree-Webhook-Signature' => generate_signature,
        'X-Spree-Webhook-Timestamp' => webhook_timestamp.to_s,
        'X-Spree-Webhook-Event' => @delivery.event_name
      }
      body = @delivery.payload.to_json
      http_options = { open_timeout: self.class::TIMEOUT, read_timeout: self.class::TIMEOUT, verify_mode: ssl_verify_mode }
      uri = URI.parse(@delivery.url)
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == 'https'
      http_options.each { |key, value| http.public_send(:"#{key}=", value) }

      request = Net::HTTP::Post.new(uri.request_uri)
      headers.each { |key, value| request[key] = value }
      request.body = body
      http.request(request)
    end

    def acos_allow_private_webhooks?
      ENV.fetch('ACOS_ALLOW_PRIVATE_WEBHOOKS', '').strip.downcase.in?(%w[1 true yes on])
    end
  end

  Rails.application.config.to_prepare do
    Spree::WebhookEndpoint.class_eval do
      private

      def url_must_not_resolve_to_private_ip
        return if ENV.fetch('ACOS_ALLOW_PRIVATE_WEBHOOKS', '').strip.downcase.in?(%w[1 true yes on])

        super
      end
    end

    unless Spree::Webhooks::DeliverWebhook.ancestors.include?(AcosDemoWebhookDeliveryPatch)
      Spree::Webhooks::DeliverWebhook.prepend(AcosDemoWebhookDeliveryPatch)
    end
  end
end
