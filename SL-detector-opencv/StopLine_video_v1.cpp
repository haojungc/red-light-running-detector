#include <opencv2/opencv.hpp> // opencv
#include <iostream> // cout and cin
#include <string>
#include <math.h> // power, tan
#include <stdlib.h>  // absolute value
#include <algorithm> // for sort
#define pi 3.14159265358979323846
#define kThres 60
#define fRate 12
using namespace std;

// Function for finding median
double median(vector<double> vec) {

	// get size of vector
	int vecSize = vec.size();

	// if vector is empty throw error
	if (vecSize == 0) {
		throw domain_error("median of empty vector");
	}

	// sort vector
	sort(vec.begin(), vec.end());

	// define middle and median
	int middle;
	double median;

	// if even number of elements in vec, take average of two middle values
	if (vecSize % 2 == 0) {
		// a value representing the middle of the array. If array is of size 4 this is 2
		// if it's 8 then middle is 4
		middle = vecSize/2;
		// take average of middle values, so if vector is [1, 2, 3, 4] we want average of 2 and 3
		// since we index at 0 middle will be the higher one vec[2] in the above vector is 3, and vec[1] is 2
		median = (vec[middle-1] + vec[middle]) / 2;
	}

	// odd number of values in the vector
	else {
		middle = vecSize/2; // take the middle again
		// if vector is 1 2 3 4 5, middle will be 5/2 = 2, and vec[2] = 3, the middle value
		median = vec[middle];
	}

	return median;
}

// Function for finding mode
float find_mode(vector<float> vec) {

	// get size of vector
	int vecSize = vec.size();

	// if vector is empty throw error
	if (vecSize == 0) {
		throw domain_error("mode of empty vector");
	}

	// sort vector
	sort(vec.begin(), vec.end());

	// define middle and median
	double number = vec[0];
	double mode = vec[0];
	int count = 1;
	int countMode = 1;

	for (int i=1; i<vec.size(); i++){
		if (round(vec[i]) == number){
			count++;
		}
		else{
			if (count > countMode){
				countMode = count;
				mode = number;
			}
			count = 1;
			number = round(vec[i]);
		}
	}

	return mode;
}
/*
float find_pair(vector<float> vec) {
	int dist = 100;
	int pair = 0;
	for(int i = 1; i < vec.size(); ++i){
		int dist_t = abs(vec[i] - vec[i-1]);
		if(dist_t < dist){
			dist = dist_t;
			pair = vec[i];
		}
	}
	return pair;
}
*/
int main(int argc, char** argv) {
	//---------------Get Video--------------------
	cv::VideoCapture cap;
	cap.open( string(argv[1]) );
	if(!cap.isOpened()){
		cout << "Could not open or find the video" << endl;
		return -1;
	}

	cv::Mat image;
	cap.read(image);
	cv::resize(image, image, cv::Size(0,0), 1920.0/image.cols, 1920.0/image.cols);
	//-----setting up kalman filter parameters------
	// dynamParams = 2 (y and y'(velocity)), measureParams = 1 (y)
	cv::KalmanFilter kalman(2, 1, 0);

	// measurements, only one parameter for y
	cv::Mat z_k = cv::Mat::zeros( 1, 1, CV_32F );

	// Transition Matrix describes the dynamics of our model
	float Ft[] = { 1, 1, 0, 1 };
	kalman.transitionMatrix = cv::Mat( 2, 2, CV_32F, Ft ).clone();

	// Initialize other Kalman filter parameters.
	cv::setIdentity( kalman.measurementMatrix, cv::Scalar(1)  		);
	cv::setIdentity( kalman.processNoiseCov, cv::Scalar(1e-5)			);
	cv::setIdentity( kalman.measurementNoiseCov, cv::Scalar(1e-1) );
	cv::setIdentity( kalman.errorCovPost, cv::Scalar(1)						);

	// the state is composed of location(y) and velocity(y')
	// initialized as y = , y' = 0
	float Fx[] = {(float)image.size().height*0.50, 0};
	kalman.statePost = cv::Mat( 2, 1, CV_32F, Fx ).clone();

	// kalman state re-initialize counter
	int kCount = 0;

	// Define the codec and create VideoWriter object
	int fourcc = cv::VideoWriter::fourcc('X','V','I','D');
	cv::Size fSize(image.size().width, image.size().height);
	string videoName(argv[1]);
	cv::VideoWriter out(videoName.append("_output.avi"),fourcc, 20.0, fSize);	// not sure the fourcc code is in the correct type

	int frameNum = 0;
	for(;;){
		//---------------GET IMAGE---------------------
		if( !cap.read(image) ) break;
		frameNum = cap.get(cv::CAP_PROP_POS_FRAMES);

		// name of window to show original image
		// cv::String originalWindowName = "Original Image";
		// Show the original image
		// imshow(originalWindowName, image);
		// cv::waitKey(0); // Wait for any keystroke in the window

		//-----------------resize----------------------- by lin
		cv::resize(image, image, cv::Size(0,0), 1920.0/image.cols, 1920.0/image.cols);

		//--------------GRAYSCALE IMAGE-----------------
		// Define grayscale image
		cv::Mat imageGray;

		// Convert image to grayscale
		cv::cvtColor(image, imageGray, cv::COLOR_BGR2GRAY);

		// window for grayscaled image
		cv::String grayscaleWindowName = "Grayscaled image";

		// Show grayscale image
		//cv::imshow(grayscaleWindowName, imageGray);
		//cv::waitKey(0); // wait for a key press

		//---------------Erosion IMAGE------------------By THLIN
		// Define erosion image
		cv::Mat imageEros;
		int erosion_size = 1;
		// Returns a structuring element of the specified size and shape for morphological operations.
		cv::Mat element = getStructuringElement( cv::MORPH_CROSS, cv::Size( 2*erosion_size + 1, 2*erosion_size+1 ), cv::Point( erosion_size, erosion_size ) );
		erode( imageGray, imageEros, element );

		// Show smoothed image
		//cv::imshow("erosionWindowName", imageEros);
		//cv::waitKey(0); // wait for a key press

		//--------------GAUSSIAN SMOOTHING-----------------
		// Use low pass filter to remove noise, removes high freq stuff like edges
		int kernelSize = 5; // bigger kernel -> more smoothing

		// Define smoothed image
		cv::Mat smoothedIm;
		cv::GaussianBlur(imageEros, smoothedIm, cv::Size(kernelSize, kernelSize), 0,0);

		// window for smoothed image
		cv::String smoothedWindowName = "Smoothed image";

		// Show smoothed image
		//cv::imshow(smoothedWindowName, smoothedIm);
		//cv::waitKey(fRate); // wait for a key press

		//--------------------CREATE MASK---------------------------
		// Create mask to only keep area defined by four corners
		// Black out every area outside area

		// Define masked image
		// Create all black image with same dimensions as original image
		// 3rd arg is CV_<bit-depth>{U|S|F}C(<number_of_channels>), so this is 8bit, unsigned int, channels: 1
		cv::Mat mask(image.size().height, image.size().width, CV_8UC1, cv::Scalar(0)); // CV_8UC3 to make it a 3 channel

		// Define the points for the mask
		// Use cv::Point type for x,y points
		// THLIN has changed the point arguments
		cv::Point p1 = cv::Point(image.size().width * (0.5 - 2.0/5.0), image.size().height*0.75);
		cv::Point p2 = cv::Point(image.size().width * (0.5 - (2.0/5.0 - 0.2*tan(50 * pi/180))), image.size().height*0.50);
		cv::Point p3 = cv::Point(image.size().width * (0.5 + (2.0/5.0 - 0.2*tan(50 * pi/180))), image.size().height*0.50);
		cv::Point p4 = cv::Point(image.size().width * (0.5 + 2.0/5.0), image.size().height*0.75);

		// create vector from array with points we just defined
		cv::Point vertices1[] = {p1,p2,p3,p4};
		std::vector<cv::Point> vertices (vertices1, vertices1 + sizeof(vertices1) / sizeof(cv::Point));

		// Create vector of vectors, add the vertices we defined above
		// (you could add multiple other similar contours to this vector)
		std::vector<std::vector<cv::Point> > verticesToFill;
		verticesToFill.push_back(vertices);

		// Fill in the vertices on the blank image, showing what the mask is
		cv::fillPoly(mask, verticesToFill, cv::Scalar(255,255,255));

		// Show the mask
		//cv::imshow("Mask", mask);
		//cv::waitKey(0);

		//------------------Threshold----------------------- by lin
		vector<double> mean, stddev;
		cv::meanStdDev(imageGray, mean, stddev, mask);
		cv::Mat imageThres;
		cv::threshold(smoothedIm, imageThres, mean[0]+1.6*stddev[0], 0, cv::THRESH_TOZERO);
		cv::String thresholdWindowName = "Threshold image";
		cv::imshow(thresholdWindowName, imageThres);
		cv::waitKey(fRate);

		//---------------EDGE DETECTION---------------------
		// finds gradient in x,y direction, gradient direction is perpendicular to edges
		// Define values for edge detection
		int minVal = 60;
		int maxVal = 150;

		// Define edge detection image, do edge detection
		cv::Mat edgesIm;
		cv::Canny(imageThres, edgesIm, minVal, maxVal);

		// window for edge detection image
		cv::String edgeWindowName = "edge detection image";

		// Show edge detection image
		//	cv::imshow(edgeWindowName, edgesIm);
		//	cv::waitKey(0); // wait for a key press

		//---------------------APPLY MASK TO IMAGE----------------------
		// create image only where mask and edge Detection image are the same
		// Create masked im, which takes input1, input2, and output. Only keeps where two images overlap
		cv::Mat maskedIm = edgesIm.clone();
		cv::bitwise_and(edgesIm, mask, maskedIm);

		// Show masked image
		cv::imshow("Masked Image", maskedIm);
		cv::waitKey(fRate);

		//------------------------HOUGH LINES----------------------------
		float rho = 2;
		float theta = pi/180;
		float threshold = 90;
		int minLineLength = 100;
		int maxLineGap = 100;

		vector<cv::Vec4i> lines; // A Vec4i is a type holding 4 integers
		cv::HoughLinesP(maskedIm, lines, rho, theta, threshold, minLineLength, maxLineGap);

		// Check if we got more than one line
		if (!lines.empty() && lines.size() > 2) {
			// Initialize lines image
			cv::Mat allLinesIm(image.size().height, image.size().width, CV_8UC3, cv::Scalar(0,0,0));
			// Loop through lines
			// std::size_t can store the maximum size of a theoretically possible object of any type
			for (size_t i = 0; i != lines.size(); ++i) {
				// Draw line onto image
				cv::line(allLinesIm, cv::Point(lines[i][0], lines[i][1]), cv::Point(lines[i][2], lines[i][3]), cv::Scalar(0,0,255), 3, 8 );
			}
			// Display images
			//cv::imshow("Hough Lines", allLinesIm);
			//cv::waitKey(0);

			//---------------Select horizontal lines which is qualified--------------------
			// Define arrays for positive/negative lines
			vector< vector<double> > horizonLines;

			// keep record of lines founded when we added one
			bool addedLine = false;

			// array counter for appending new lines
			int lineCounter = 0;

			// Loop through all lines
			for (size_t i = 0; i != lines.size(); ++i) {

				// Get points for current line
				float x1 = lines[i][0];
				float y1 = lines[i][1];
				float x2 = lines[i][2];
				float y2 = lines[i][3];

				// get line length
				float lineLength =  pow(pow(x2-x1,2) + pow(y2-y1,2), .5);
				// if line is long enough
				if (lineLength > 30) {
					// dont divide by zero
					if (x2 != x1) {
						// get slope
						float slope = (y2-y1)/(x2-x1);
						// Find angle of line wrt x axis.
						float tanTheta = tan ( (y2-y1) / (x2-x1) ); // tan(theta) value
						float angle = atan (tanTheta) * 180/pi; // angle using degree as unit

						// Only pass good line angles,  dont want verticalish/horizontalish lines
						if (abs(angle) < 2.5 && abs(angle) >= 0) {

							// create mask for the area above the detected line
							cv::Mat lineMask(image.size().height, image.size().width, CV_8UC1, cv::Scalar(0)); // CV_8UC3 to make it a 3 channel
							cv::Point q1 = cv::Point(x1, y1);
							cv::Point q2 = cv::Point(x2, y1);
							cv::Point q3 = cv::Point(x2, y1-min( (float)(abs(x2-x1)*2.5),(float)50. ));
							cv::Point q4 = cv::Point(x1, y1-min( (float)(abs(x2-x1)*2.5),(float)50. ));
							cv::Point lineVertices1[] = {q1,q2,q3,q4};
							std::vector<cv::Point> lineVertices (lineVertices1, lineVertices1 + sizeof(vertices1) / sizeof(cv::Point));
							std::vector<std::vector<cv::Point> > lineVerticesToFill;
							lineVerticesToFill.push_back(lineVertices);
							cv::fillPoly(lineMask, lineVerticesToFill, cv::Scalar(255,255,255));
							//cv::imshow("lineMask", lineMask);
							//cv::waitKey(33);
							vector<double> lineMean, lineStddev;
							cv::meanStdDev(imageGray, lineMean, lineStddev, lineMask);

							if(lineMean[0] < mean[0]+1.25*stddev[0]) { // to filter out lines on the background and white cars
								// Add a row to the matrix
								horizonLines.resize(lineCounter+1);

								// Reshape current row to 5 columns [x1, y1, x2, y2, slope]
								horizonLines[lineCounter].resize(6);

								// Add values to row
								horizonLines[lineCounter][0] = x1;
								horizonLines[lineCounter][1] = y1;
								horizonLines[lineCounter][2] = x2;
								horizonLines[lineCounter][3] = y2;
								horizonLines[lineCounter][4] = -slope;
								horizonLines[lineCounter][5] = -angle;

								// Note that we added a positive slope line
								addedLine = true;

								// iterate the counter
								lineCounter++;
							}else{
								cout << "white car / background detected";
							}
						}
					} // if x2 != x1
				} // if lineLength > 30
			} // looping though all lines

			// If we still dont have lines then fuck
			if (addedLine == false) {
				kCount++;
				if(kCount > kThres){
					float Fx[] = {(float)image.size().height*0.50, 0};
					kalman.statePost = cv::Mat( 2, 1, CV_32F, Fx ).clone();
					kCount = 0;
				}
				cout << "Not enough lines found" << endl;

				// output frame to video file
				out.write(image);

				cv::imshow("Lane lines on image",image);
				if( cv::waitKey(fRate) >= 0 ) break;
				continue;	// if no line detected the loop starts over again.
			}

			//------------------Calculate the most frequent slope------------------------- by lin
			vector<float> horizonAngles;
			addedLine = false;	// in case that all the line has angle of 0
			for (unsigned int i = 0; i != horizonLines.size(); ++i) {
				//printf("%f\n",horizonLines[i][4]);
				if(horizonLines[i][5] != 0){
					horizonAngles.push_back(horizonLines[i][5]);
					addedLine = true;
				}
			}
			if(addedLine == false){
				kCount++;
				if(kCount > kThres){
					float Fx[] = {(float)image.size().height*0.50, 0};
					kalman.statePost = cv::Mat( 2, 1, CV_32F, Fx ).clone();
					kCount = 0;
				}
				cout << "Not enough non-zero-angle lines found" << endl;

				// output frame to video file
				out.write(image);

				cv::imshow("Lane lines on image",image);
				if( cv::waitKey(fRate) >= 0 ) break;
				continue;
			}
			sort(horizonAngles.begin(), horizonAngles.end());
			double angleMode = find_mode(horizonAngles); // find_mode() only returns the first mode that is found.
			/* for debug
			for (unsigned int i = 0; i != horizonAngles.size(); ++i){
				printf("%f\n",horizonAngles[i]);
			}
			printf("%f\n", angleMode);
			*/

			//-----------------GET LINE ANGLE AVERAGES-----------------------
			// Average the angle of lines that has angle wtihin close to anleMode
			vector<vector<float>> angleGoodLines;
			float Sum = 0.0; // sum so we'll be able to get mean

			lineCounter = 0;
			// Loop through positive slopes and add the good ones
			for (size_t i = 0; i != horizonLines.size(); ++i) {
				// check difference between current slope and the median. If the difference is small enough it's good
				if (abs(horizonLines[i][5] - angleMode) < 0.3) {
					angleGoodLines.resize(lineCounter+1);
					angleGoodLines[lineCounter].resize(6);
					angleGoodLines[lineCounter][0] = horizonLines[i][0]; // Add slope to posSlopesGood
					angleGoodLines[lineCounter][1] = horizonLines[i][1];
					angleGoodLines[lineCounter][2] = horizonLines[i][2];
					angleGoodLines[lineCounter][3] = horizonLines[i][3];
					angleGoodLines[lineCounter][4] = horizonLines[i][4];
					angleGoodLines[lineCounter][5] = horizonLines[i][5];
					Sum += horizonLines[i][5]; // add to sum
					++lineCounter;
				}
			}

			// Get mean of good positive slopes
			float angleMean = Sum/angleGoodLines.size();
			//	printf("%f\n", angleMean);

			//------------------Calculate the most frequent y coord------------------------- by lin
			vector<float> yIntercepts;
			for (size_t i = 0; i != angleGoodLines.size(); ++i) {
				double x1 = angleGoodLines[i][0]; // x value
				double y1 = image.rows - angleGoodLines[i][1]; // y value...yaxis is flipped
				double slope = angleGoodLines[i][4];
				double yIntercept = y1-slope*x1; // y intercept at x = 0
				double xIntercept = -yIntercept/slope; // find x intercept based off y = mx+b
				if (isnan(yIntercept) == 0) { // check for nan
					yIntercepts.push_back(yIntercept); // add value
				}
			}

			sort(yIntercepts.begin(), yIntercepts.end());
			double yIntMode = find_mode(yIntercepts);
			/* for debug
			printf("%s\n", "y intercept");
			for (unsigned int i = 0; i != yIntercepts.size(); ++i){
				printf("%f\n", yIntercepts[i]);
			}
			printf("%f\n", yIntMode);
			*/

			//------------------------Kalman Filter-------------------------
			// predict point position
			cv::Mat y_k = kalman.predict();
			//measurement
			z_k = yIntMode;
			// adjust Kalman filter state
			kalman.correct( z_k );

			//-----------------------PLOT LANE LINES------------------------
			// Create image, horizontal lines on real image
			cv::Mat laneLineImage = image.clone();

			float slope = tan (angleMean * pi/180);
			double x1 = 0;
			int y1 = y_k.at<float>(0);
			//and extrapolate to the top and bottom of the lane
			double x2 = image.size().width;
			double y2 = y1 + (x2-x1)*slope;



			// Add positive slope line to image
			x1 = int(x1 + .5);	// round
			x2 = int(x2 + .5);
			y1 = int(y1 + .5);
			y2 = int(y2 + .5);
			cv::line(laneLineImage, cv::Point(x1, image.size().height-y1), cv::Point(x2, image.size().height - y2), cv::Scalar(0,255,0), 3, 8 );

			// output frame to video file
			out.write(laneLineImage);

			// Plot positive and negative lane lines
			cv::imshow("Lane lines on image", laneLineImage);
			if( cv::waitKey(fRate) >= 0 ) break;

		} // end if we got more than one line
		else { // We do none of that if we don't see enough lines
			kCount++;
			if(kCount > kThres){
				float Fx[] = {(float)image.size().height*0.50, 0};
				kalman.statePost = cv::Mat( 2, 1, CV_32F, Fx ).clone();
				kCount = 0;
			}
			cout << "Not enough hough lines found" << endl;

			// output frame to video file
			out.write(image);

			cv::imshow("Lane lines on image",image);
			if( cv::waitKey(fRate) >= 0 ) break;
		}
	}//for_loop of frames
	cap.release();
	out.release();
	return 0;
}
