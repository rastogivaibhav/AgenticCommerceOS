# frozen_string_literal: true

require 'json'
require 'net/http'
require 'fileutils'
require 'time'

DEMO_PRODUCT_SLUG = 'oxford-shirt'
DEMO_PRODUCT_NAME = 'Oxford Shirt'
DEMO_PRODUCT_SKU = 'OXFORD-SHIRT-01'
DEMO_PRODUCT_DESCRIPTION = 'Crisp cotton oxford shirt for work and weekends.'
DEMO_PRODUCT_PRICE = 79.99
DEMO_PRODUCT_STOCK = 25
DEMO_ORDER_NOTE = 'ACOS_DEMO_LAST_WEEK_ORDER'
DEMO_ORDER_EMAIL = 'ava.demo@example.com'
DEMO_ORDER_ADDRESS = {
  first_name: 'Ava',
  last_name: 'Morgan',
  address1: '1 Demo Street',
  city: 'New York',
  postal_code: '10001',
  phone: '07700900001',
  country_iso: 'US',
  state_abbr: 'NY'
}.freeze

store = Spree::Store.default || Spree::Store.first
raise 'No Spree store found after seed. Run db:seed first.' unless store

Spree::Current.store = store

publishable_token = ENV.fetch('SPREE_DEMO_PUBLISHABLE_KEY', 'pk_acos_demo_publishable_key')
api_key = Spree::ApiKey.find_or_initialize_by(store: store, name: 'ACOS Demo Store API Key', key_type: 'publishable')
api_key.token = publishable_token
api_key.save!

webhook_url = ENV.fetch('ACOS_SPREE_WEBHOOK_URL', 'http://ops-api:8081/api/v1/webhooks/spree')
webhook_secret = ENV.fetch('SPREE_WEBHOOK_SECRET', 'dev-spree-webhook-secret')
fixture_path = ENV.fetch('SPREE_DEMO_FIXTURE_PATH', '/tmp/spree_demo_fixtures.json')
store_api_url = ENV.fetch('SPREE_DEMO_STORE_API_URL', 'http://spree-web:3000')
public_store_url = ENV.fetch('SPREE_DEMO_PUBLIC_URL', 'http://127.0.0.1:3000')

subscriptions = %w[
  order.completed
  shipment.shipped
  return_authorization.received
  return_item.received
  payment.failed
  order.canceled
  product.back_in_stock
  variant.stock_changed
  webhook.test
]

def ensure_demo_product!(store)
  template = Spree::Product.first
  raise 'No seeded Spree products available to derive tax/shipping categories.' unless template

  product = Spree::Product.find_or_initialize_by(slug: DEMO_PRODUCT_SLUG)
  product.name = DEMO_PRODUCT_NAME
  product.description = DEMO_PRODUCT_DESCRIPTION
  product.status = 'active'
  product.available_on ||= Time.current
  product.shipping_category ||= template.shipping_category
  product.tax_category ||= template.tax_category
  product.save!

  if product.respond_to?(:stores) && !product.stores.exists?(store.id)
    product.stores << store
  end

  master = product.master
  master.sku = DEMO_PRODUCT_SKU
  master.weight = 0.4
  if master.respond_to?(:set_price)
    master.set_price(store.default_currency || 'USD', DEMO_PRODUCT_PRICE)
  else
    master.price = DEMO_PRODUCT_PRICE
  end
  master.save!

  stock_location = Spree::StockLocation.first || Spree::StockLocation.create!(name: 'Shop location')
  stock_item = stock_location.stock_item_or_create(master)
  stock_item.set_count_on_hand(DEMO_PRODUCT_STOCK)
  stock_item.backorderable = false
  stock_item.save!

  product.reload
  product
end

def http_json(method, url, headers:, body: nil)
  uri = URI(url)
  request_class = case method.to_s.upcase
                  when 'POST' then Net::HTTP::Post
                  when 'PATCH' then Net::HTTP::Patch
                  when 'GET' then Net::HTTP::Get
                  else
                    raise "Unsupported HTTP method #{method}"
                  end
  request = request_class.new(uri)
  headers.each { |key, value| request[key] = value }
  request.body = JSON.generate(body) if body

  response = Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == 'https') do |http|
    http.request(request)
  end
  payload = response.body.to_s.empty? ? {} : JSON.parse(response.body)
  unless response.code.to_i.between?(200, 299)
    raise "HTTP #{response.code} for #{uri.path}: #{payload}"
  end
  payload
end

def ensure_last_week_order!(store_api_url:, publishable_token:, product:)
  existing = Spree::Order.complete.order(completed_at: :desc).detect do |order|
    order.email == DEMO_ORDER_EMAIL &&
      order.customer_note == DEMO_ORDER_NOTE &&
      order.line_items.any? { |line_item| line_item.variant_id == product.master.id }
  end
  if existing
    existing.update!(completed_at: 7.days.ago)
    return existing
  end

  base_headers = {
    'X-Spree-API-Key' => publishable_token,
    'Content-Type' => 'application/json'
  }
  cart = http_json('POST', "#{store_api_url}/api/v3/store/carts", headers: base_headers)
  guest_headers = base_headers.merge('X-Spree-Token' => cart.fetch('token'))

  http_json(
    'POST',
    "#{store_api_url}/api/v3/store/carts/#{cart.fetch('id')}/items",
    headers: guest_headers,
    body: { variant_id: product.master.to_param, quantity: 1 }
  )

  http_json(
    'PATCH',
    "#{store_api_url}/api/v3/store/carts/#{cart.fetch('id')}",
    headers: guest_headers,
    body: {
      email: DEMO_ORDER_EMAIL,
      customer_note: DEMO_ORDER_NOTE,
      shipping_address: DEMO_ORDER_ADDRESS,
      billing_address: DEMO_ORDER_ADDRESS
    }
  )

  payment_method = Spree::PaymentMethod::Check.active.first
  raise 'No active Check payment method found for demo checkout.' unless payment_method

  http_json(
    'POST',
    "#{store_api_url}/api/v3/store/carts/#{cart.fetch('id')}/payments",
    headers: guest_headers,
    body: { payment_method_id: payment_method.to_param }
  )

  completed = http_json(
    'POST',
    "#{store_api_url}/api/v3/store/carts/#{cart.fetch('id')}/complete",
    headers: guest_headers
  )
  order = Spree::Order.find_by!(number: completed.fetch('number'))
  order.update!(completed_at: 7.days.ago, customer_note: DEMO_ORDER_NOTE)
  order
end

def check_payment_method_payload
  payment_method = Spree::PaymentMethod::Check.active.first
  raise 'No active Check payment method found for demo checkout.' unless payment_method

  {
    id: payment_method.to_param,
    name: payment_method.name,
    type: payment_method.type
  }
end

def product_payload(product)
  master = product.master
  {
    id: product.prefixed_id,
    name: product.name,
    slug: product.slug,
    description: product.description,
    variant_id: master.to_param,
    sku: master.sku,
    price: master.price.to_s,
    currency: product.currency || master.currency || 'USD',
    thumbnail_url: product.respond_to?(:thumbnail_url) ? product.thumbnail_url : nil
  }
end

def order_payload(order)
  {
    id: order.prefixed_id,
    number: order.number,
    token: order.token,
    email: order.email,
    completed_at: order.completed_at&.utc&.iso8601,
    total: order.total.to_s,
    state: order.state,
    payment_state: order.payment_state,
    shipment_state: order.shipment_state
  }
end

webhook_status = 'configured'
webhook_events = subscriptions
endpoint_scope = Spree::WebhookEndpoint.respond_to?(:with_deleted) ? Spree::WebhookEndpoint.with_deleted : Spree::WebhookEndpoint
endpoint = endpoint_scope.find_or_initialize_by(store: store, name: 'ACOS Demo Webhook')
endpoint.url = webhook_url
endpoint.active = true
endpoint.subscriptions = subscriptions
endpoint.secret_key = webhook_secret
endpoint.deleted_at = nil if endpoint.respond_to?(:deleted_at=)
endpoint.disabled_at = nil if endpoint.respond_to?(:disabled_at=)
endpoint.disabled_reason = nil if endpoint.respond_to?(:disabled_reason=)

begin
  endpoint.save!
  webhook_events = endpoint.subscribed_events
rescue ActiveRecord::RecordInvalid => e
  webhook_status = "skipped: #{e.record.errors.full_messages.join(', ')}"
  webhook_events = []
end

Spree::Events.enable! if Spree::Events.respond_to?(:enable!)
Spree::Events.activate! if Spree::Events.respond_to?(:activate!)

demo_product = ensure_demo_product!(store)
last_week_order = ensure_last_week_order!(
  store_api_url: store_api_url,
  publishable_token: publishable_token,
  product: demo_product
)

fixture_payload = {
  generated_at: Time.now.utc.iso8601,
  store: {
    name: store.name,
    url: store.url,
    rails_env: ENV.fetch('RAILS_ENV', 'unknown'),
    admin_urls: {
      dashboard: "#{public_store_url}/admin",
      orders: "#{public_store_url}/admin/orders",
      product_edit: "#{public_store_url}/admin/products/#{demo_product.slug}/edit"
    }
  },
  checkout_payment_method: check_payment_method_payload,
  product: product_payload(demo_product),
  last_week_order: order_payload(last_week_order),
  webhook: {
    url: webhook_url,
    status: webhook_status,
    subscriptions: webhook_events
  }
}

FileUtils.mkdir_p(File.dirname(fixture_path))
File.write(fixture_path, JSON.pretty_generate(fixture_payload))

puts({
  status: 'ready',
  store: store.name,
  store_url: store.url,
  publishable_key: publishable_token,
  webhook_url: webhook_url,
  webhook_status: webhook_status,
  webhook_subscriptions: webhook_events,
  fixture_path: fixture_path,
  demo_product: fixture_payload[:product],
  last_week_order: fixture_payload[:last_week_order]
}.to_json)
