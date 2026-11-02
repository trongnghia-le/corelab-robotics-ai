# Pinhole camera: project, deproject and calibrate

This optional bridge takes about 25 minutes. You can skip it and open any activity. Reading it creates no evidence.

A camera model turns 3-D points into pixels. Everything below is a synthetic, ideal model: no image is read, and a small error in these numbers says nothing about a real lens.

## Frames and conventions

The camera frame has x to the right of the image, y DOWN the image and z forward along the optical axis. The depth of a point is its z coordinate. A point is in front of the camera only when z > 0. A pixel is (u, v), with u to the right and v down. These conventions are a choice; a different library may flip y or z, so always write yours down.

The intrinsics are fx and fy (focal lengths in pixels) and the principal point (cx, cy) in pixels. With no lens distortion and no skew, a camera-frame point (X, Y, Z) projects to

u = fx · X/Z + cx, v = fy · Y/Z + cy.

Two facts follow. Dividing by Z means a point twice as far away lands half as far from the principal point, so one pixel cannot tell you the depth. And if Z = 0 the formula divides by zero, while a negative Z flips the signs and gives a mirrored pixel for a point that the camera cannot see. A correct routine rejects Z ≤ 0 (or any Z below a stated minimum) instead of returning a number.

## Extrinsics: world to camera

Objects are usually described in a world frame. The extrinsics are a rotation R (three rows) and a translation t that map a world point to the camera frame:

p_cam = R p_world + t.

t is where the world origin sits in camera coordinates, not where the camera sits in the world. The inverse is p_world = Rᵀ (p_cam − t): subtract t first, then apply the transpose. R must be a proper rotation: its rows are perpendicular unit vectors and its determinant is +1 (a determinant of −1 is a mirror, not a rotation).

## Deprojection needs a depth

Inverting the projection for a pixel gives x = (u − cx)/fx and y = (v − cy)/fy. These are the slopes of a ray through the camera centre. To get one 3-D point you need the depth: p_cam = Z · (x, y, 1). A depth sensor or a known floor plane supplies it. Be careful: some sensors report the distance along the ray rather than Z, and the two differ by a factor √(x² + y² + 1).

## Reprojection error

Given points known in the camera frame and the pixels where they were measured, the reprojection error of one point is the pixel distance between the projected point and the measured pixel. Report the root mean square (RMS) over the n points: √(Σ (Δu² + Δv²) / n). It is in pixels, and it is only meaningful if you also say which points were used.

## A simple linear calibrator

If the camera-frame points are known, then u = fx · x + cx with x = X/Z is an ordinary straight line, and so is v = fy · y + cy with y = Y/Z. Fit each line by least squares: slope = Sxy / Sxx and intercept = mean(pixel) − slope · mean(coordinate), where Sxx and Sxy are sums of products of deviations from the means. The two fits are independent. They need the coordinate to vary: if every x is the same, a focal length and a principal point cannot be told apart.

Worked example (u side only). Four markers have x = (−0.2, 0, 0.2, 0.4) and measured columns u = (222, 319, 419, 520). The mean x is 0.1 and the mean u is 370. The deviations of x are (−0.3, −0.1, 0.1, 0.3), so Sxx = 0.09 + 0.01 + 0.01 + 0.09 = 0.2. Sxy = (−0.3)(−148) + (−0.1)(−51) + (0.1)(49) + (0.3)(150) = 44.4 + 5.1 + 4.9 + 45 = 99.4. Then fx = 99.4 / 0.2 = 497 px and cx = 370 − 497 · 0.1 = 320.3 px. A good check of any fit: the residuals sum to zero and are uncorrelated with x.

## Judge it on views the fit never saw

A fit always looks good on its own data. Split the correspondences by a rule you state before fitting, for example the first three for training and the rest held out. Fit on the training points only, then compute the RMS on both groups. If the held-out RMS is much larger than the training RMS, the model does not describe those views (for example, points far from the image centre where a real lens bends rays that this model ignores). Using any held-out point in the fit is leakage: the held-out number then measures nothing.

## Honest scope

This bridge covers an ideal pinhole, a declared rigid transform, deprojection with a given depth and a two-line least-squares intrinsic fit. It does not cover images, corner detection, lens distortion, calibration with unknown camera poses (Zhang's method), pose estimation, stereo, rolling shutter or calibrating a real device. A low reprojection error in a toy does not validate a real calibration.

Try the camera practice with a pencil, then run the camera self-check kit. Ask a Socratic tutor for a conceptual question or one next step; declare any external help. Practice, videos and AI solutions never automatically establish verified mastery.

Original educational content © 2026 Le Trong Nghia, CC BY 4.0. Author draft; independent review pending.
