"""
Константы для RabbitMQ событий, очередей и routing keys
"""

# Exchange Names
class ExchangeNames:
    BOX4KIDS_EVENTS = "box4kids_events"
    
    # Для будущих расширений
    NOTIFICATIONS = "notifications"
    ANALYTICS = "analytics"
    SYSTEM = "system"


# Queue Names  
class QueueNames:
    TOYBOX = "toybox_queue"
    NOTIFICATIONS = "notifications_queue"
    
    # Для будущих расширений
    EMAIL = "email_queue"
    SMS = "sms_queue"
    ANALYTICS = "analytics_queue"
    DELIVERY = "delivery_queue"


# Routing Keys
class RoutingKeys:
    # Payment events
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # ToyBox events
    TOYBOX_CREATED = "toybox.created"
    TOYBOX_DELIVERED = "toybox.delivered"
    TOYBOX_RETURNED = "toybox.returned"
    TOYBOX_REVIEWED = "toybox.reviewed"
    
    # Notification events
    NOTIFICATION_SMS_SENT = "notification.sms.sent"
    NOTIFICATION_EMAIL_SENT = "notification.email.sent"
    NOTIFICATION_PUSH_SENT = "notification.push.sent"
    
    # System events
    SYSTEM_HEALTH_CHECK = "system.health.check"
    SYSTEM_ERROR = "system.error"
    
    # Analytics events
    ANALYTICS_USER_ACTION = "analytics.user.action"
    ANALYTICS_CONVERSION = "analytics.conversion"


# Event Types (для type safety)
class EventTypes:
    PAYMENT = "payment"
    TOYBOX = "toybox"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    ANALYTICS = "analytics"


# Bindings Configuration (какие routing keys слушает каждая очередь)
QUEUE_BINDINGS = {
    QueueNames.TOYBOX: [
        RoutingKeys.PAYMENT_PROCESSED,
    ],
    
    QueueNames.NOTIFICATIONS: [
        RoutingKeys.TOYBOX_CREATED,
        RoutingKeys.PAYMENT_PROCESSED,
        RoutingKeys.PAYMENT_FAILED,
        RoutingKeys.TOYBOX_DELIVERED,
        RoutingKeys.TOYBOX_RETURNED,
    ],
    
    # Будущие расширения
    QueueNames.EMAIL: [
        RoutingKeys.NOTIFICATION_EMAIL_SENT,
    ],
    
    QueueNames.SMS: [
        RoutingKeys.NOTIFICATION_SMS_SENT,
    ],
    
    QueueNames.ANALYTICS: [
        RoutingKeys.ANALYTICS_USER_ACTION,
        RoutingKeys.ANALYTICS_CONVERSION,
    ],
    
    QueueNames.DELIVERY: [
        RoutingKeys.TOYBOX_DELIVERED,
        RoutingKeys.TOYBOX_RETURNED,
    ],
} 