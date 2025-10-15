# Customer Orders MCP Feature Specification

This document outlines the requirements and implementation details for the Customer Orders MCP server and its integration with the Waiter agent.

## Original Instructions

> Can you create a new MCP server that is connected to the Waiter that is for "Customer Orders" where they remember which customer had which order? Then update the waiter's instructions so that they ask for teh name of the patron before taking their order. When they take an order, call "save_order(name, order_details, estimated_wait_time)" (which is what you should create in the MCP server. Also create a list_orders that returns all outstanding orders. The orders should be saved in a JSON file called orders.json. Each order should have a status as well of RECEIVED, COOKING, READY or SERVED. Once the waiter gives an order to the CHEF agent, then the order should be updated with a set_order_status(order_id) tool to COOKING. By default new orders have a status of RECEIVED. Once the chef is done the order is READY. The order only gets set to SERVED if the customer asks the waiter where their food is. If the order is READY, the waiter serves it and sets the status to SERVED. Also save_order should return an autoincrementing order_id to be listed by set_order_status and list_orders. Make this Customer Orders MCP server and hook it up to the waiter only.

The order MCP server should use stdio and look exactly like the pantry MCP server but ONLY be connected to the waiter agent.
