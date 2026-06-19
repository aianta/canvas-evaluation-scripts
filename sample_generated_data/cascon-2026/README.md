# CASCON 2026 Evaluation Dataset

A random selection of 46 task instances for model construction and then 46 task instances for evaluation was generated using the following script.
`python3 task_selection.py --input ./sample_generated_data/cascon-2026/tasks.json --format both --random-sample 1 --training-csv training_instances.csv`

LogUI upon which OdoX was built, stores trajectories as sessions inside flights. Flight data is stored in LogUI server's Mongo database. The recordings we want to use for model construction are subsequently scraped into elasticsearch with a script. `cascon-flight-list.json' lists the flights that were scraped for the model created for the Cascon paper, the flight ids should align with those listed under [OdoBot Model Construction Task Instances](#odobot-model-construction-task-instances). 


# OdoBot Model Construction Task Instances

The following task instances were randomly selected from `tasks.yaml` for model construction. 

|#| Task ID | Instance ID| Trajectory ID| 
|-|-|-|-|
|1|0b62c5d4-a6fe-4083-9123-45e3087c1440|8008c15f-e8f4-4884-bd77-4c16d70f35c8|7fa894c8-a2bb-45fb-9684-a6895ab47459|
|2|0be01f7a-0c6e-49c3-af20-52f9b97ef728|11a49ea7-0527-456a-b17a-1179799e2abf|ecf39b7a-3894-4eb4-a078-1b2e1d55d8bc|
|3|0e27e906-bd1d-4ecb-957f-f8acb9c51e08|e33a4d6f-6091-4271-a964-fcedd7be8e44|a787f4de-8ac4-4bac-8534-83c370714e6e|
|4|14875b88-4d4f-44be-a989-cff2a705958e|0db4fb34-a491-4160-8431-7c7aa6496d86|a9d9569d-35a2-46d8-9658-f9bf40b2cd72|
|5|14fe049e-9db4-497a-97c9-507a2c60d55e|51e8c8c0-2687-4e5b-b833-cfa7653bce52|954a28e6-be9b-4f07-b8ad-22810681eff8|
|6|158b7ece-5c61-466f-9447-9ab9e43c0b03|d851a161-9bda-4fa8-83ac-10c01e9acba2|474d11dd-f99b-43dd-be2a-d624368bab98|
|7|175397c6-1439-40ab-8b74-8f0e479ef8c5|b104ced1-ce92-436e-84e8-b87d937f0cbd|edbc793b-61e7-4274-8649-51f02f5ecfc7|
|8|1977dbaa-1d14-4b08-a40b-0090df524371|98b7b3f5-8c73-4afa-8fc6-09347c7330b8|1a683a42-427c-48f0-8c10-05281cf99495|
|9|229bb30d-7652-40a9-934d-3e14d54e7ab9|fbe8dbbd-d4d8-4573-ad64-bcb9f530a0bf|a51e4e72-e84f-42d1-9525-056cc5f1cb77|
|10|2776ed0f-e34e-4ffc-8884-9720a48a7420|22a64f4e-693e-4232-8c02-caf707ab2d21|8c29e052-2925-4d25-bdd3-6c1107c8577a|
|11|279dcf3e-77f5-4a1b-8ced-ebdb8bb7e462|a85d1241-c52b-4121-a3fa-f8f24911c0e5|49149705-9199-4c0c-b72a-33972c3b484e|
|12|29d80dd0-2506-41bc-ad55-40db3359b84c|7977ed9a-167e-431f-9f87-b514ff84ae00|1f585479-a3f5-4b3c-8d91-26ef2680f692|
|13|2b0a143f-fb9c-4f8e-9606-211e6bcb8171|32fdabfa-4c70-4d0f-8da9-be208db86f8a|45a7dbb3-9570-4dd4-889f-7e8f8c127813|
|14|3b389112-ccb7-4272-853e-8dbe81a1c6c8|3fc4b0bc-ca0a-4121-99b4-fe4f4d97d454|e39f803a-630f-4d19-bc65-eea9ab7e11fb|
|15|42ad8db4-826a-414a-9ad6-b5c9abd93078|c7099ee3-1b60-4d74-8dfa-57cdac5dc56c|5bc36a7c-b391-4a79-a084-49c6c665def4|
|16|45974a3d-36dc-409e-9fe4-8cbd0adc3517|0d2fa70e-f439-49b3-9416-695c92ceadc9|f8c58a85-0842-43ea-b9e2-e4de379f57a1|
|17|5718e37a-b1d1-4ec9-a223-7fd262419682|37d0b707-ed8c-4a98-b5f3-6034ff57c79c|95aac1a3-2b97-4bfe-ba96-fb33652fab9c|
|18|6242d2f1-f67e-4d56-a856-b9a5f536672f|89c4cde4-f1e7-4044-a73c-eb068c093177|58004770-b71c-44ed-a636-39b218ec168e|
|19|681d72b5-e5fb-4895-960c-f5127e10fcac|e6de20b2-5f39-4e6f-b503-44c9314a6434|c0b749e3-268b-4ca5-b6ac-b98c18511487|
|20|6f4fd860-3339-4de0-9172-d18ac3a6d89f|3f64f555-081b-49df-a8f1-7a2392feb1ce|367e4ffc-841c-4d4e-b1d7-9dca96aaebf9|
|21|8aa2d6ba-d913-4972-ac2a-0056fc386691|0b2fdb78-4bc0-4c5c-b61d-92fbc4dc0eab|a6aa9079-fe6a-4e50-ab65-a7bb09793e6b|
|22|8be2d07d-8263-4add-9198-662264777c6c|60d509c1-e768-4041-a7a3-3e62b928bb70|c10aee5a-a454-4f38-86ad-ec3dfd427eb3|
|23|9151a1c8-9803-4a89-b6a4-4b6dfa2190cf|16b15335-07fc-4a41-be55-6dd488ccc2e4|bfdfb92f-8457-407d-827e-c4a0bb90e1ef|
|24|98d2e0b9-478c-4eec-b40b-82a61e78ba87|2dbce2d1-a127-4246-a862-0bdca24d820d|03dcd0f7-daa8-4cf0-ad14-d73fb7de937c|
|25|9b30427c-2025-48db-baed-2cff271cd819|ef57b44d-20da-4d2c-9c5b-05f056a8aa61|12c3c093-e70c-419e-b07a-f089afbce40d|
|26|9b7f10f1-60fe-4bbe-968c-9b828cdbeb8f|4220041f-a99e-454b-9801-2d69d8f7f6a0|72a57b50-0158-4c31-803b-be08704b7d07|
|27|a1c4e8bf-af9a-49c5-9672-5e83c0170b9b|fc4500fb-7855-4047-9b87-9c7a800fbefb|4689bc69-a25e-4971-a903-722be4e06f22|
|28|b18ec1c0-213c-480c-8c5e-b770e86e8c76|a9877e74-40af-47d5-8f5e-2721f7d693d8|ee6679b9-b614-49ba-bfe1-c747bcc248ef|
|29|b68ad0fe-8cd4-40b1-ad7f-88b43510da75|0c9d5da5-7e9c-44c5-a48d-c1739ce05299|615f4c34-f421-4acb-8879-5ea285626dae|
|30|bc69c1dc-3ccc-4cef-80ec-ed2a5d931c5e|a6d7e999-f25a-4415-ba58-5b8f4bda5f56|796678e8-2fa1-4149-8449-9f252af7b389|
|31|c9819826-9891-4b9a-824b-f94f91a6598b|79acabb1-ef63-42a4-814f-6926cede0d88|96123e35-5655-43bc-9370-72505193eb19|
|32|cfb8fa30-c680-4b13-9dd0-d49e4567ff15|3fedab57-3974-4c69-bd74-53fbda23a607|edaea78e-3625-43d0-99ea-e5980401e029|
|33|d098f836-5e11-4e64-ac4c-55dd100ec323|e2f2aef6-132e-497e-928d-d123a88c44ed|07adbb0f-aa29-41f0-b6eb-1fbc842da1dd|
|34|d6ac9877-e256-4487-86cc-2bb0b085c804|2d54c177-bbc6-48cc-8474-45404251c1b2|8419c8ea-ae60-47da-a48f-e08c9a48c6ec|
|35|d8f661f0-6bcc-4778-8b5e-ed716f425cd8|a260465f-5ca9-4d98-9438-db37fa769e85|3b1a176f-9f88-4d71-948d-0ab75279e7d6|
|36|e070c0de-41d2-42aa-8a7c-c93f98fdc4c4|624affcb-afa1-4219-9cda-ad72ba8a05b6|c6750915-2745-4bd8-a408-db8fecf5f4b2|
|37|e0cfbef6-1383-463e-ac40-db871e962295|b3d5488a-44a8-4805-bd53-e23e322f52f4|6fade4f2-fdc9-4078-aebf-85d3edfa0f98|
|38|e178ca11-ad42-4c2e-811c-cb3c25177dc8|9c9e28ed-f43c-4102-b65a-d3a2a0b05dcf|ed98d67e-70f9-47d7-91d0-3e920035d261|
|39|e476f98d-e1e1-4fb7-b8d4-2b0bc832ff69|55ec33dd-cf2d-4089-ac1d-a4a65000517c|85409a14-6dc2-4d55-966e-87d3688ea5e7|
|40|e5f9684d-4b57-45c7-81e3-0d065f75545b|1127e17d-0072-4c97-88f4-88a8e1e96bcf|5fc3ff4b-ea78-41e2-a321-8994636b82d4|
|41|f36e03d8-3c1a-4223-ad61-8aca0b4546fb|ec744463-62db-4027-b814-ed850f042bdb|6a5cb866-4a12-4f1c-a742-6242c22fe03a|
|42|f5e1c597-c2ad-45f6-aa7c-7b7dee0d3675|41561cd5-30bb-429d-854a-34cdd54c2751|2b34cfcf-e4ee-41bd-9dec-ac23e6d875bd|
|43|f9e0dc04-ac1e-4189-8c58-91a66d561e06|143d154e-c1ac-477a-aec0-38327b9fef2e|3d6a6c9c-a7cb-43f3-bf04-d6384678a937|
|44|fa70e65c-16fb-4d03-9041-bcf07cf6ae02|25ad9f42-3d97-4f10-acc6-4a437ea873fa|323994c6-408d-4a3a-b985-b895aa57dad4|
|45|fa9d33b1-09e0-43af-996a-74f9acbee197|baa81eb9-2789-4dfc-bb33-8f86f032fc4f|3e0d3b24-4d50-42a1-bd1f-941a17ec8853|
|46|ff0f349b-4812-41ae-8b85-ae6c2899db2c|23b01c2c-93ae-4e6a-b541-c12e3ed4b9e8|dfec5fb4-d902-4cf5-bfbb-ab055e2906ea|
  

# Evaluation Task Instances

The following tasks were randomly selected for evalutation. 

|Task ID| Instance ID | 
|-|-|  