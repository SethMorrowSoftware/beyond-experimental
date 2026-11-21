script "CoreInterfaceImagePaintCompressionNone"
/*
Copyright (C) 2026 OXT-Beyond contributors.

This file is part of OXT-Beyond.

OXT-Beyond is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License v3 as published by the Free
Software Foundation.

OXT-Beyond is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with OXT-Beyond.  If not see <http://www.gnu.org/licenses/>.  */

/*
The paintCompression "none": an image whose pixels a script sets (its
imageData, alphaData or maskData, a crop, the paint tools) holds them
uncompressed, and compresses them only when their data is needed, as
"rle" would: when the stack is saved, the image closes, or its text,
size or paintCompression is read. A script setting the imageData many
times a second no longer compresses every frame (more than 30 ms for a
640 x 480 picture with transparency) nor decompresses it to draw it.

What a script sees is what "rle" gives it, the data to the byte, with
one difference while the pixels are held: a pixel the maskData hides
keeps the colour it was set to, where "rle" keeps none under its mask.
The other values keep their old results (the engine suite compares).
*/

local sOldCompression

on TestSetup
   put the paintCompression into sOldCompression
end TestSetup

on TestTearDown
   set the paintCompression to sOldCompression
   if there is a stack "PaintCompressionNone" then
      delete stack "PaintCompressionNone"
   end if
end TestTearDown

-- Each test's images go on a stack of its own (the runner sets the
-- defaultStack to the test's stack before each test).
private command useNewStack
   create stack "PaintCompressionNone"
   set the defaultStack to "PaintCompressionNone"
end useNewStack

-- Pixels that differ in every channel, so a lost byte shows.
private function pixelsOf pWidth, pHeight, pSeed
   local tData, x, y
   repeat with y = 1 to pHeight
      repeat with x = 1 to pWidth
         put numToByte(0) & numToByte((x * 7 + pSeed) mod 256) & \
               numToByte((y * 5 + pSeed) mod 256) & \
               numToByte((x * y + pSeed) mod 256) after tData
      end repeat
   end repeat
   return tData
end pixelsOf

-- "alpha": every level of transparency; "mask": only clear and opaque.
private function alphasOf pWidth, pHeight, pKind
   local tData, x, y
   repeat with y = 1 to pHeight
      repeat with x = 1 to pWidth
         if pKind is "mask" then
            if (x + y) mod 3 is 0 then
               put numToByte(0) after tData
            else
               put numToByte(255) after tData
            end if
         else
            put numToByte((x * 3 + y) mod 256) after tData
         end if
      end repeat
   end repeat
   return tData
end alphasOf

-- An image of the size given, set with the pixels (and transparency, when
-- pKind is "alpha" or "mask") in the paintCompression given.
private function imageWith pCompression, pName, pKind, pSeed
   set the paintCompression to pCompression
   create image pName
   set the width of image pName to 37
   set the height of image pName to 23
   set the imageData of image pName to pixelsOf(37, 23, pSeed)
   if pKind is "alpha" then
      set the alphaData of image pName to alphasOf(37, 23, "alpha")
   else if pKind is "mask" then
      set the maskData of image pName to alphasOf(37, 23, "mask")
   end if
   return the long id of image pName
end imageWith

on TestNoneIsAPaintCompression
   set the paintCompression to "none"
   TestAssert "the paintCompression can be none", the paintCompression is "none"
   set the paintCompression to "rle"
   TestAssert "and set back", the paintCompression is "rle"
end TestNoneIsAPaintCompression

on TestNoneKeepsThePixelsSet
   local tNone, tRle, tKind
   useNewStack
   repeat for each item tKind in "opaque,alpha"
      put imageWith("none", "none" & tKind, tKind, 1) into tNone
      put imageWith("rle", "rle" & tKind, tKind, 1) into tRle
      set the paintCompression to "none"
      TestAssert tKind && "imageData as rle gives it", \
            the imageData of tNone is the imageData of tRle
      TestAssert tKind && "alphaData as rle gives it", \
            the alphaData of tNone is the alphaData of tRle
      TestAssert tKind && "maskData as rle gives it", \
            the maskData of tNone is the maskData of tRle
   end repeat
end TestNoneKeepsThePixelsSet

on TestNoneGivesTheDataRleGives
   local tNone, tRle, tKind
   useNewStack
   repeat for each item tKind in "opaque,alpha,mask"
      put imageWith("none", "none" & tKind, tKind, 2) into tNone
      put imageWith("rle", "rle" & tKind, tKind, 2) into tRle
      set the paintCompression to "none"
      TestAssert tKind && "text as rle gives it", \
            the text of tNone is the text of tRle
      TestAssert tKind && "size as rle gives it", \
            the size of tNone is the size of tRle
      TestAssert tKind && "paintCompression as rle gives it", \
            the paintCompression of tNone is the paintCompression of tRle
      TestAssert tKind && "imageData as rle gives it, once compressed", \
            the imageData of tNone is the imageData of tRle
   end repeat
end TestNoneGivesTheDataRleGives

on TestNoneImageReportsTheFormatItSaves
   local tImage
   useNewStack
   put imageWith("none", "opaque", "opaque", 3) into tImage
   TestAssert "an opaque picture is kept as rle", \
         the paintCompression of tImage is "rle"
   put imageWith("none", "alpha", "alpha", 3) into tImage
   TestAssert "one with transparency as png", \
         the paintCompression of tImage is "png"
end TestNoneImageReportsTheFormatItSaves

on TestNoneCompressesWithThePaintCompressionThen
   local tImage, tPng
   useNewStack
   put imageWith("none", "later", "opaque", 4) into tImage
   put imageWith("png", "png", "opaque", 4) into tPng
   set the paintCompression to "png"
   TestAssert "held pixels compress as the paintCompression in force", \
         the paintCompression of tImage is "png"
   TestAssert "to the same data", the text of tImage is the text of tPng
end TestNoneCompressesWithThePaintCompressionThen

on TestNoneMaskedPixelsKeepTheirColourWhileHeld
   local tNone, tRle, tSet
   useNewStack
   put pixelsOf(37, 23, 5) into tSet
   put imageWith("none", "none", "mask", 5) into tNone
   put imageWith("rle", "rle", "mask", 5) into tRle
   set the paintCompression to "none"
   TestAssert "the mask is the same", the maskData of tNone is the maskData of tRle
   -- The second pixel of the first row is one the mask hides.
   TestAssert "the pixel is hidden", byte 2 of the maskData of tNone is numToByte(0)
   TestAssert "a hidden pixel keeps its colour while held", \
         byte 6 to 8 of the imageData of tNone is byte 6 to 8 of tSet
   TestAssert "rle keeps none under its mask", \
         byte 6 to 8 of the imageData of tRle is numToByte(0) & numToByte(0) & numToByte(0)
   get the text of tNone
   TestAssert "once compressed, as rle gives it", \
         the imageData of tNone is the imageData of tRle
end TestNoneMaskedPixelsKeepTheirColourWhileHeld

on TestNoneImagesAreSavedCompressed
   local tPath, tStack, tData, tAlpha, tOpaque
   useNewStack
   put the tempName into tPath
   set the filename of stack "PaintCompressionNone" to tPath
   get imageWith("none", "alpha", "alpha", 6)
   get imageWith("none", "opaque", "opaque", 7)
   put the imageData of image "alpha" into tData
   put the alphaData of image "alpha" into tAlpha
   put the imageData of image "opaque" into tOpaque
   save stack "PaintCompressionNone"
   TestAssert "the stack saves", the result is empty
   delete stack "PaintCompressionNone"
   set the paintCompression to "rle"
   put the short name of stack tPath into tStack
   TestAssert "the picture with transparency comes back", \
         the imageData of image "alpha" of stack tStack is tData and \
         the alphaData of image "alpha" of stack tStack is tAlpha
   TestAssert "saved as png", the paintCompression of image "alpha" of stack tStack is "png"
   TestAssert "the opaque one comes back", the imageData of image "opaque" of stack tStack is tOpaque
   TestAssert "saved as rle", the paintCompression of image "opaque" of stack tStack is "rle"
   delete stack tStack
   delete file tPath
end TestNoneImagesAreSavedCompressed

on TestNoneImageClonesAndCrops
   local tImage, tClone, tRle
   useNewStack
   put imageWith("none", "none", "alpha", 8) into tImage
   clone tImage
   put it into tClone
   TestAssert "a clone has the pixels", the imageData of tClone is the imageData of tImage \
         and the alphaData of tClone is the alphaData of tImage
   put imageWith("rle", "rle", "alpha", 8) into tRle
   set the paintCompression to "none"
   crop image "none" to the left of tImage + 3, the top of tImage + 2, \
         the left of tImage + 20, the top of tImage + 15
   set the paintCompression to "rle"
   crop image "rle" to the left of tRle + 3, the top of tRle + 2, \
         the left of tRle + 20, the top of tRle + 15
   TestAssert "cropped", the width of tImage is 17 and the height of tImage is 13
   TestAssert "a crop has the pixels rle gives", the imageData of tImage is the imageData of tRle \
         and the alphaData of tImage is the alphaData of tRle
end TestNoneImageClonesAndCrops

on TestNoneImageDrawsAsRleDoes
   local tNone, tRle, tNoneShot, tRleShot
   useNewStack
   put imageWith("none", "none", "alpha", 9) into tNone
   put imageWith("rle", "rle", "alpha", 9) into tRle
   set the paintCompression to "none"
   export snapshot from tNone to tNoneShot as PNG
   export snapshot from tRle to tRleShot as PNG
   TestAssert "a snapshot of it is drawn alike", tNoneShot is tRleShot and tNoneShot is not empty
   export tNone to tNoneShot as PNG
   export tRle to tRleShot as PNG
   TestAssert "exported alike", tNoneShot is tRleShot and tNoneShot is not empty
end TestNoneImageDrawsAsRleDoes

on TestNoneImageGivenText
   local tImage, tPng
   useNewStack
   put imageWith("rle", "source", "alpha", 10) into tPng
   put the text of tPng into tPng
   set the paintCompression to "none"
   create image "given"
   set the text of image "given" to tPng
   TestAssert "a picture's own data is kept as it is", the text of image "given" is tPng
end TestNoneImageGivenText

on TestNoneImageSetManyTimes
   local tNone, tRle, tFrame, i
   useNewStack
   put imageWith("none", "none", "alpha", 11) into tNone
   put imageWith("rle", "rle", "alpha", 11) into tRle
   repeat with i = 12 to 41
      put pixelsOf(37, 23, i) into tFrame
      set the paintCompression to "none"
      set the imageData of tNone to tFrame
      set the paintCompression to "rle"
      set the imageData of tRle to tFrame
   end repeat
   set the paintCompression to "none"
   TestAssert "the last frame set is the one held", \
         the imageData of tNone is the imageData of tRle
   TestAssert "with its transparency", the alphaData of tNone is the alphaData of tRle \
         and the alphaData of tNone is alphasOf(37, 23, "alpha")
end TestNoneImageSetManyTimes
