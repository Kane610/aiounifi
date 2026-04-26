"""Legacy REST handler layer.

Each module subclasses APIHandler and optionally hooks
controller.messages for websocket-driven updates via
process_messages / remove_messages class attributes.
"""
