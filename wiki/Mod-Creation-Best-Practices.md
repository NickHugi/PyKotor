# Mod Creation Best Practices

This page provides common workaround strategies for mod creation. For modding tools and syntax guides, see [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.) and [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme).

## Common Workaround Strategies

A common problem you may encounter when creating a mod, is the inability to remove a gff struct. Let's say you want to remove a GIT instance to be compatible with another mod. Both HoloPatcher and TSLPatcher do not support this. However, you can work around it.

## Removing GFF struct's?

In this example, I needed to remove all (20+) box placeables, 2 of 4 droids in the module and move the remaining 2 droids to other positions. I tried several possible solutions, including `GetFirstObjectInShape / GetNextObjectInShape` and `GetNearestObjectToLocation` functions. I think these functions worked well with a small number of objects, but at times left a few of the 20+ boxes placed on the level. So I switched to `GetObjectByTag / DestroyObject` functions.

The summary:

1.Write code in a script that will search for and delete the necessary objects in the module.

2.Gate the 'delete script' with a local boolean set on the area/some object to make sure it only runs once.

3.Attach the script to an object, dialog, trigger or onEnter script of the module (not recommended, bad for compatibility with other mods).

It was easy for me to remove 4 droids instead of 2, and then create 2 in new positions. But if one needs to, for example, remove 5 out of 30 instances of an object in a module, then one should probably use the `GetFirstObjectInShape/GetNextObjectInShape` functions.

Example of code:

```nwscript
void main(){
    if(GetLocalNumber( OBJECT_SELF, 32 ) != 150){
      DestroyObjectsByTag("objectTag");
      //DestroyPlaceablesAndCreaturesInArea(oLoc1, SHAPE_CUBE, 36.0f);
      SetLocalNumber(OBJECT_SELF, 32, 150);
    }
}

void DestroyObjectsByTag(string tag){
  int i = 0;
  object oPlc = GetObjectByTag(tag);
  while(GetIsObjectValid(oPlc)){
    DestroyObject(oPlc);
    i++;
    oPlc = GetObjectByTag(tag, i);
  }

void DestroyPlaceablesAndCreaturesInArea(location oLoc1, int nShape, float areaSize){
  object oPlc = GetFirstObjectInShape(nShape, areaSize, oLoc1, 0, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);
  while (GetIsObjectValid(oPlc))
  {
    DestroyObject(oPlc);
    oPlc = GetNextObjectInShape(nShape, areaSize, oLoc1, 0, OBJECT_TYPE_CREATURE | OBJECT_TYPE_PLACEABLE);
  }
}
```

## Storing 2DAMEMORY without duplicating/creating a row

The ExclusiveColumn field is perfect for this situation. Here's an example where we know the 'label' and we want to simply store the RowIndex.

```ini
[genericdoors.2da]
CopyRow0=copy_row_0
CopyRow1=copy_row_1
CopyRow2=copy_row_2
CopyRow3=copy_row_3
CopyRow4=copy_row_4

[copy_row_0]
ExclusiveColumn=label
LabelIndex=Hammerhead2
label=Hammerhead2
2DAMEMORY114=RowIndex
[copy_row_1]
ExclusiveColumn=label
LabelIndex=Hammerhead3
label=Hammerhead3
2DAMEMORY115=RowIndex
[copy_row_2]
ExclusiveColumn=label
LabelIndex=SleheyronDoor1
label=SleheyronDoor1
2DAMEMORY116=RowIndex
[copy_row_3]
ExclusiveColumn=label
LabelIndex=SleheyronDoor2
label=SleheyronDoor2
2DAMEMORY117=RowIndex
[copy_row_4]
ExclusiveColumn=label
LabelIndex=YavinHgrDoor1
label=YavinHgrDoor1
2DAMEMORY118=RowIndex
```
