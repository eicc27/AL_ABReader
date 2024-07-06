from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    QSequentialAnimationGroup,
)


class Animator:
    def __init__(self, element: QWidget) -> None:
        self.element = element
        self.animGroup = QSequentialAnimationGroup()

    def isPlaying(self):
        return (
            hasattr(self, "anim")
            and self.animGroup
            and self.animGroup.state() == QPropertyAnimation.State.Running
        )

    def shakeVerticalOnce(self):
        anim = QPropertyAnimation(self.element, b"pos")
        start = self.element.pos()
        # print(f"start: {start.x()}, {start.y()}")
        anim.setEndValue(start)
        anim.setKeyValueAt(0.5, start + QPoint(0, 50))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setDuration(200)
        self.animGroup.addAnimation(anim)
        return self

    def shakeHorizontalMultiple(self, loopCount=5):
        anim = QPropertyAnimation(self.element, b"pos")
        start = self.element.pos()
        # print(f"start: {start.x()}, {start.y()}")
        anim.setEndValue(start)
        anim.setKeyValueAt(0.5, start + QPoint(50, 0))
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setDuration(65)
        anim.setLoopCount(loopCount)
        self.animGroup.addAnimation(anim)
        return self

    def moveHorizontal(self, duration: int, dx: int):
        anim = QPropertyAnimation(self.element, b"pos")
        start = self.element.pos()
        anim.setEndValue(start + QPoint(dx, 0))
        anim.setEasingCurve(QEasingCurve.Type.OutCurve)
        anim.setDuration(duration)
        self.animGroup.addAnimation(anim)
        return self

    def moveVertical(self, duration: int, dy: int):
        anim = QPropertyAnimation(self.element, b"pos")
        start = self.element.pos()
        anim.setEndValue(start + QPoint(0, dy))
        anim.setEasingCurve(QEasingCurve.Type.OutCurve)
        anim.setDuration(duration)
        self.animGroup.addAnimation(anim)
        return self

    def clear(self):
        self.animGroup.clear()
        return self
