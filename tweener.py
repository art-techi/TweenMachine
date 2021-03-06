''' Original code from https://github.com/dgovil/PythonForMayaSamples/blob/master/tweener/tweener.py
    Updated by: Meg Coleman
    Updated on: June 09, 2020

    Changes made:
        - added a float field for user input
        - synchronized field and slider to update simultaneously
        - edited row/column layout and spacing
'''
from maya import cmds

# It is important when programming, to split out our logic from our UI
# This lets us call our tween code from other places without calling our UI, and also lets us test if its working properly
def tween(percentage, obj=None, attrs=None, selection=True):
    """
    This function will tween the keyed attributes on an object.
    Args:
        percentage (float): This is a mandatory argument (since it has no default) and will be the percentage to tween
        obj (str): the name of the object to use. This is optional since it has a default value
        attrs (list): A list of the attributes to tween. This is optional since it has a default value
        selection (bool): Whether to use the selection or not. Again, optional because it has a default
    """
    percentage = float(percentage)
    # We need to error early if we aren't given an object AND we are told not to use the selection
    if not obj and not selection:
        # We raise a ValueError saying we got nothing to work with
        raise ValueError("No object given to tween")

    # If there is no object given, but selection must be true by now, we will get the current selection
    if not obj:
        # We list the selection. sl is shorthand for selection. [0] is beacause we only care about the first item
        obj = cmds.ls(sl=1)[0]

    # If we don't have a list of attrs to work with, we'll query which attributes are keyable
    if not attrs:
        attrs = cmds.listAttr(obj, keyable=True)

    # Now we need to get the current frame from Maya
    currentTime = cmds.currentTime(query=True)

    # Now we have everything to start, lets loop through all the attributes
    for attr in attrs:
        # It's common to need the object and attribute together like pCube1.translateX so we prepare the full name before hand
        attrFull = '%s.%s' % (obj, attr)

        # We query what keyframes exist for that attribute
        keyframes = cmds.keyframe(attrFull, query=True)

        # If there are no keyframes, then it isn't keyed so we skip it
        if not keyframes:
            # We continue on to the next item in the loop
            continue

        # We create an empty list to hold the values of our previous keyframes
        previousKeyframes = []
        # We loop through all the keyframes
        for k in keyframes:
            # If they are less than our current frame we will add them to the list
            if k < currentTime:
                # We append the frame value to the list
                previousKeyframes.append(k)

        # This is the same as above but it uses a concept called list comprehension
        # It lets us flatten all the logic we just used into a single line
        # It says add every frame from keyframes if the frame is greater than the current time
        laterKeyframes = [frame for frame in keyframes if frame > currentTime]

        # If we have neither previous or later frames, then skip ahead
        if not previousKeyframes and not laterKeyframes:
            continue

        # If we do have previous keyframes, we need to find the nearest one to us
        if previousKeyframes:
            # This will be the highest of the previous keyframes, so it can be found using max
            previousFrame = max(previousKeyframes)
        else:
            # But if there are no previous keyframes, we'll set previousFrame to None to say we didn't find one
            previousFrame = None

        # Instead of doing a multiline if statement like above, we can do it in one line like here
        # If there are laterKeyframes, we'll find the minimum value to get the closest
        # Otherwise we'll set it to None to indicate we couldn't find it
        nextFrame = min(laterKeyframes) if laterKeyframes else None

        # If we didn't find it, we'll set previousFrame to be the same as the nextFrame.
        # This helps simplify our logic later
        if previousFrame is None:
            previousFrame = nextFrame

        # SImilar to the above if statement, we can condense it to a single line
        nextFrame = previousFrame if nextFrame is None else nextFrame

        # Now we query the values on the respective frames for this attribute
        # Because we prepared the attrFull variable above, we can reuse it here
        previousValue = cmds.getAttr(attrFull, time=previousFrame)
        nextValue = cmds.getAttr(attrFull, time=nextFrame)

        if nextFrame is None:
            # If there is no nextFrame, then set our currentValue to the previousValue
            currentValue = previousValue
        elif previousFrame is None:
            # if there is no previousFrame, set our currentValue to the nextValue
            currentValue = nextValue
        elif previousValue == nextValue:
            # If they are both equal, then just pick one of them
            currentValue = previousValue
        else:
            # If they are different, we calculate the tween value
            difference = nextValue - previousValue
            biasedDifference = (difference * percentage)
            currentValue = previousValue + biasedDifference

        # Finally we set this value
        # Sometimes Maya doesn't update the viewport when just setting a key so also do a setAttr
        cmds.setAttr(attrFull, currentValue)
        # Then finally set the key
        cmds.setKeyframe(attrFull, time=currentTime, value=currentValue)

# Again we create a class to contain functions(also called methods) that relate to each other
# In this case they relate because they are part of the window
# This class is called TweenerWindow, and it is based of (inherits) the python 'object'
class TweenerWindow(object):
    # This is a class level variable
    # We use these for variables that don't really change
    windowName = "TweenerWindow"

    # Here we create a method called show that will be used to show the window
    # Its first argument is 'self' so that it has a reference to itself
    def show(self):
        # First we check if a window of this name already exists.
        # This prevents us having many tweener windows when we just want one
        if cmds.window(self.windowName, query=True, exists=True):
            # If another window of the same name exists, we close it by deleting it
            cmds.deleteUI(self.windowName)

        # Now we create a window using our name
        cmds.window(self.windowName)

        # Now we call our buildUI method to build out the insides of the UI
        self.buildUI()

        # Finally we must actually show the window
        cmds.showWindow()

        # try to reopen the window
        if not cmds.window(self.windowName, query=True, exists=True):
            cmds.showWindow()

    def buildUI(self):
        # To start with we create a layout to hold our UI objects
        # A layout is a UI object that lays out its children, in this case in a column
        column = cmds.columnLayout(rowSpacing=10)

        # Now we create a text label to tell a user how to use our UI
        cmds.text(label="Set the tween amount using the slider or box")

        #ADDED HERE
        #rowColumn allows for spacing adjustment
        row = cmds.rowColumnLayout(numberOfColumns=2, columnSpacing=(2, 10))

        ###EDITED SLIDER TO WORK ON RANGE [0, 1]
        # We create a slider, set its minimum, maximum and default value.
        # The changeCommand needs to be given a function to call, so we give it our tween function
        # We need to hold on to our slider's name so we can edit it later, so we hold it in a variable
        # calls updateValues now to match field value
        self.slider = cmds.floatSlider(min=0, max=1, value=0.5, step=0.01, dragCommand=self.updateValues)

        # ADDED HERE
        # created a field to receive input
        self.myTextField = cmds.floatField(minValue=0, maxValue=1, value=0.5, step=0.01, changeCommand=self.updateValues)
        cmds.setParent(column) # change active parent

        # adjust the layout
        row = cmds.rowColumnLayout(numberOfColumns=2, columnSpacing=(2, 5))
        #Reset button
        cmds.button(label="RESET", command=self.reset)

        # We add a button to close our UI
        cmds.button(label="Close", command=self.close)
        cmds.setParent(column)

    # reset button
    def reset(self, *args):
        # update slider field
        cmds.floatSlider(self.slider, edit=True, value=0.5)
        # update float field
        cmds.floatField(self.myTextField, edit=True, value=0.5)
    #close the window
    def close(self, *args):
        # This will delete our UI, thereby closing it
        cmds.deleteUI(self.windowName)

    #ADDED HERE
    #updates the values in both the slider and the field simultaneously
    def updateValues(self, percentage, obj=None, attrs=None, selection=True):
        cmds.floatSlider(self.slider, edit=True, value=percentage)
        cmds.floatField(self.myTextField, edit=True, value=percentage)
        tween(percentage, obj=obj, attrs=attrs, selection=selection)

if __name__ == "__main__":
    window = TweenerWindow()
    window.show()
