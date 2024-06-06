
A Manager's Guide to bring your On-Prem Cloud up to speed


Many companies want to move to the Public Cloud although they already have a Private Cloud environment in-house including all the talent thats needed.
Most of the time the Deployment Speed, Standardization & Convenience of a Hyperscaler like AWS , Azure & GCP seems to be more attractive.

But an On-Prem Cloud Environment does have its advantages:

- Company Culture and Quirks :)
- Access to legacy Systems
- Better security if it not public facing
- Also suitable for highly sensitive Data

and most importantly

- Costs ! (if it is done right)

It is a common misconception that a Hyperscaler is cheaper.

Here are a couple of key steps you need to take to get the most out of your in-house Virtual Private Cloud Environment.


- A Key Difference is the additional behind-the-scenes layer that needs to decouple the Cloud World from the Legacy World
	- this Layer should be used to abstract all the Infrastructure Orchestration
	- Infrastructure Orchestration often uses Runbook Automation Tools, which makes perfect sense if you understand the role
	- define clear separations between these Layers
	- the product of the Orchestration Layer should be IaaS - other platform teams will build on that
	- Pets become Cattle, Methods change, Cultures change
	- Do not mix the Worlds! - they follow different Paradigms
	- at one point the SREs should stop to innovate and should be able to stabilize the Infrastructure

- Do not enforce pure Scrum on Infrastructure Teams!
	- Infrastructure is different: Datacenters burn, Updates kill Appliances, Manufacturers get bankrupt,etc..
	- Infrastructure needs Operations! If you insist on agile methods, leave room for tasks related to Operations
	- if you enforce methods from the Software World on Infrastructure, teams will start to pull Products out of thin air to please management:
		e.g. Admin Jump Hosts that should be a Linux Server with SSH Keys become Spaceships with MongoDB, Kafka & Co. slowing down actual progress
		
		
- But we want to use Terraform!
	- no problem: let your engineers create a little middleware between the Orchestration Layer and your Platform Teams (use my repo for inspiration) https://github.com/martymonero/terraform-bridge/
	- this will decouple the two layers and creates room to breath for the SREs
	- then they will also be able to bring the deployments up to speed and will match speeds comparable to Hyperscalers






