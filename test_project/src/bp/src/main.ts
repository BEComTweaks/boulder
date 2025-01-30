import { world, system, ItemComponentTypes, ItemCooldownComponent } from "@minecraft/server";

const glazedTerracottaColorBlocks: string[] = [
    "minecraft:black_glazed_terracotta",
    "minecraft:blue_glazed_terracotta",
    "minecraft:brown_glazed_terracotta",
    "minecraft:cyan_glazed_terracotta",
    "minecraft:gray_glazed_terracotta",
    "minecraft:green_glazed_terracotta",
    "minecraft:light_blue_glazed_terracotta",
    "minecraft:lime_glazed_terracotta",
    "minecraft:magenta_glazed_terracotta",
    "minecraft:orange_glazed_terracotta",
    "minecraft:pink_glazed_terracotta",
    "minecraft:purple_glazed_terracotta",
    "minecraft:red_glazed_terracotta",
    "minecraft:silver_glazed_terracotta",
    "minecraft:white_glazed_terracotta",
    "minecraft:yellow_glazed_terracotta"
];

const numberFacingDirectionMapping: { [key: number]: number } = {
    0: 5,
    1: 5,
    2: 4,
    3: 5,
    4: 3,
    5: 2
};

world.beforeEvents.itemUseOn.subscribe(useOnEvent => {
    const { itemStack: item, block, source: player } = useOnEvent;

    if (item.typeId !== "bt:rw.wrench") return;

    const { typeId: blockTypeId, permutation: blockPermutation } = block;

    if (glazedTerracottaColorBlocks.includes(blockTypeId)) {
        useOnEvent.cancel = true;

        system.run(() => {
            const itemCooldownComponent: ItemCooldownComponent = item.getComponent(ItemComponentTypes.Cooldown) as ItemCooldownComponent;

            if (itemCooldownComponent.getCooldownTicksRemaining(player) !== 0) return;

            itemCooldownComponent.startCooldown(player);

            const newDirection: number = numberFacingDirectionMapping[blockPermutation.getState("facing_direction") as number] as number;

            block.setPermutation(blockPermutation.withState("facing_direction", newDirection));
        });
    }
});