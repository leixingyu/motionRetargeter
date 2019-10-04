from pyfbsdk import *
from pyfbsdk_additions import *
import os
from Qt import QtCore, QtGui, QtWidgets
from Qt import _loadUi

class MyWindow(QtWidgets.QDialog):
    def __init__(self):
        super(MyWindow, self).__init__()
        _loadUi('retargeter.ui', self)

        self.linkFunc()
        self.skeletonPath = ''
        self.mocapPath = ''

    def linkFunc(self):
        self.skeletonBrw.clicked.connect(self.setSkeletonPath)
        self.mocapBrw.clicked.connect(self.setMocapPath)

        self.importBtn.clicked.connect(self.importFbx)
        self.retargetBtn.clicked.connect(self.retargetFbx)
        self.cleanBtn.clicked.connect(self.cleanFbx)

    def setSkeletonPath(self):
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, 'Select your skeleton file', r'C:\Users\Lei\Desktop\fbx')[0]
        self.skeletonEdt.setText(filePath)
        self.skeletonPath = str(self.skeletonEdt.text())

    def setMocapPath(self):
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, 'Select your mocap file', r'C:\Users\Lei\Desktop\fbx')[0]
        self.mocapEdt.setText(filePath)
        self.mocapPath = str(self.mocapEdt.text())

    def importFbx(self):
        app = FBApplication()
        app.FileNew()

        if os.path.isfile(self.mocapPath):
            app.FileOpen(self.mocapPath, False)
            # set clipping to 1
            # for camera in FBSystem().Scene.Cameras:
            # if camera.Name == 'Producer Perspective':
            # print(camera.Name +":" + str(camera.FarPlaneDistance))

            locator = FBFindModelByLabelName('Reference')
            locator.Scaling = FBVector3d(0.054, 0.054, 0.054)

            # merge target file
            if os.path.isfile(self.skeletonPath):
                app.FileMerge(self.skeletonPath, False)
            else:
                print(r"Can't locate target model")
        else:
            print(r"Can't locate motion data")

        t = FBTime(0, 0, 0, 0, 0)
        FBPlayerControl().Goto(t)

    def retargetFbx(self):
        # bake settings
        lOptions = FBPlotOptions()
        lOptions.ConstantKeyReducerKeepOneKey = True
        lOptions.PlotAllTakes = False
        lOptions.PlotOnFrame = True
        lOptions.PlotPeriod = FBTime(0, 0, 0, 1)
        lOptions.PlotTranslationOnRootOnly = True
        lOptions.PreciseTimeDiscontinuities = True
        lOptions.RotationFilterToApply = FBRotationFilter.kFBRotationFilterGimbleKiller
        lOptions.UseConstantKeyReducer = True

        # characterize motion data
        character = FBSystem().Scene.Characters[1]
        character.SetCharacterizeOn(True)

        # retarget motion data to character
        luna = FBSystem().Scene.Characters[0]
        luna.InputCharacter = character
        luna.CreateControlRig(True)
        luna.InputType = FBCharacterInputType.kFBCharacterInputCharacter
        luna.ActiveInput = True
        # print('current source: ' + luna.InputType)

        # bake animation to control rig
        luna.PlotAnimation(FBCharacterPlotWhere.kFBCharacterPlotOnControlRig, lOptions)
        # print('current source: ' + luna.InputType)

        # set frame rate
        FBPlayerControl().SetTransportFps(FBTimeMode.kFBTimeMode30Frames)
        # print('new frame rate: ' + FBPlayerControl().GetTransportFpsValue() + 'fps')

        # set time range
        endTime = FBSystem().CurrentTake.LocalTimeSpan.GetDuration().GetFrame()
        if endTime <= 3000:
            FBSystem().CurrentTake.LocalTimeSpan = FBTimeSpan(
                FBTime(0, 0, 0, 3, 0),
                FBTime(0, 0, 0, endTime+3, 0)
            )

        # add new animation layer
        FBSystem().CurrentTake.CreateNewLayer()
        lCount = FBSystem().CurrentTake.GetLayerCount()
        newL = FBSystem().CurrentTake.GetLayer(lCount-1)
        newL.Name = 'handIK_init_adjust'
        newL.SelectLayer(True, True)

    def cleanFbx(self):
        # bake settings
        lOptions = FBPlotOptions()
        lOptions.ConstantKeyReducerKeepOneKey = True
        lOptions.PlotAllTakes = False
        lOptions.PlotOnFrame = True
        lOptions.PlotPeriod = FBTime(0, 0, 0, 1)
        lOptions.PlotTranslationOnRootOnly = True
        lOptions.PreciseTimeDiscontinuities = True
        lOptions.RotationFilterToApply = FBRotationFilter.kFBRotationFilterGimbleKiller
        lOptions.UseConstantKeyReducer = True

        # bake animation to skeleton
        luna = FBSystem().Scene.Characters[0]
        luna.PlotAnimation(FBCharacterPlotWhere.kFBCharacterPlotOnSkeleton, lOptions)

        # delete control rig
        for ctrl in FBSystem().Scene.ControlSets:
            ctrl.FBDelete()

        # delete character
        FBSystem().Scene.Characters[0].FBDelete()
        FBSystem().Scene.Characters[0].FBDelete()

        def DeleteBranch(topModel):
            while len(topModel.Children) > 0:
                DeleteBranch(topModel.Children[-1])
            topModel.FBDelete()

        # delete model
        ref = FBFindModelByLabelName('Reference')
        mesh = FBFindModelByLabelName('Mesh_Luna_Full')
        DeleteBranch(ref)
        DeleteBranch(mesh)

if __name__ == '__builtin__':
    window = MyWindow()
    window.show()


