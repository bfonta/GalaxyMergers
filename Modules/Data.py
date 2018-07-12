import os, glob, time
import tensorflow as tf
import numpy as np

from Modules.Infos import LoopInfo
from Modules.General import unison_shuffle
from Modules.Picture import Picture

class Data:
    'Class for handling data operations'
    def __init__(self, name=""):
        self.name = name
        
        
    def save_to_tfrecord(self, DataFolder, Classes, DataName, DataMin=0, DataMax=99999999, Height=300, Width=300, Depth=3, Extension='jpg'):
        """
        Creates two arrays: one with pictures and the other with numerical labels
        Each class must have a separate subfolder, and all classes must lie inside the same data folder.

        Arguments:
        1. DataFolder (string): folder where all the pictures from all the classes are stored.
        2. Classes (tuple): classes to be considered.
        3. Extension (string): extension of the pictures inside DataFolder. Only 'jpg' is supported.
        
        Stores:
        1. A 4d array with pictures and another array with labels. The first array follows the following format: (index, height_in_pixels, width_in_pixels, numer_of_channels)
        2. The given classes are converted into numerical labels, starting from zero. For example, if three classes are present, 'a', 'b' and 'c', then the labels with respectively be 0, 1 and 2.
        
        Returns: nothing
        """
        ###Functions to be used for storing the files as TFRecords###                                   
        def _bytes_feature(value):
            return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))
        def _int64_feature(value):
            return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

        ###Sanity checks### 
        allowed_extensions = ['jpg', 'jpeg', 'JPG', 'JPEG']
        if Extension not in allowed_extensions:
            print("ERROR: The", Extension, "extension is not supported.")
            sys.exit()
        if not os.path.isdir(DataFolder):
            print("ERROR: The specified", DataFolder, "folder does not exist.")
            sys.exit()
        for nameClass in Classes:
            if not os.path.exists( os.path.join(DataFolder,nameClass) ):
                print("ERROR: The specified", os.path.join(DataFolder,nameClass), "does not exist." )
                sys.exit()

        ###Tensorflow Picture Decoding###
        Pics = Picture()
        graph, nameholder, image_tensor = Pics.tf_decoder(Height, Width)
        with tf.Session(graph=graph) as sess:
            init = tf.group( tf.global_variables_initializer(), tf.local_variables_initializer() )
            sess.run(init)
            indiv_len = np.zeros(len(Classes), dtype=np.uint32)
            for iClass, nameClass in enumerate(Classes):
                glob_list = glob.glob(os.path.join(DataFolder,nameClass,"*."+Extension))
                indiv_len[iClass]=len(glob_list[DataMin:DataMax])
                total_len = sum(indiv_len)

            #Write to a .tfrecord file
            loop = LoopInfo(total_len)
            with tf.python_io.TFRecordWriter(DataName) as Writer:
                for iClass, nameClass in enumerate(Classes):
                    glob_list = glob.glob(os.path.join(DataFolder,nameClass,"*."+Extension))
                    glob_list = glob_list[DataMin:DataMax]
                    for i,pict in enumerate(glob_list):
                        index = i + iClass*indiv_len[iClass-1] if iClass != 0 else i
                        tmp_picture = sess.run(image_tensor, feed_dict={nameholder: pict} )
                        #tmp_picture = Pics.np_decoder(pict, Height, Width)               
                        if index%100 == 0:
                            loop.loop_print(index, time.time())
                        Example = tf.train.Example(features=tf.train.Features(feature={
                            'height': _int64_feature(Height),
                            'width': _int64_feature(Width),
                            'depth': _int64_feature(Depth),
                            'picture_raw': _bytes_feature(tmp_picture.tostring()),
                            'label': _int64_feature(iClass)
                        }))
                        Writer.write(Example.SerializeToString())
        print("The data was saved.")


    def load_from_tfrecord(self, filenames):
        """
        Loads one or more TFRecords binary file(s) containing pictures information and converts it/them back to numpy array format. The function does not know before-hand how many pictures are stored in 'filenames'.
        Arguments:
        1. The names of the files to load.                                                                   
        Returns:
        1. A 4d array with pictures and another array with labels. The first array follows the following format: (index, height_in_pixels, width_in_pixels, numer_of_channels)
        2. The given classes are converted into numerical labels, starting from zero. For example, if three classes are present, 'a', 'b' and 'c', then the labels with respectively be 0, 1 and 2.
        """
        for filename in filenames:
            if not os.path.isfile(filename):
                print("The data stored in", filename,
                      "could not be loaded. Please make sure the filename is correct.")
                sys.exit()
                
        pict_array, label_array = ([] for i in range(2)) #such a fancy initialization!    
        for filename in filenames:
            iterator = tf.python_io.tf_record_iterator(path=filename)
            loop = LoopInfo()
            for i, element in enumerate(iterator):
                Example = tf.train.Example()
                Example.ParseFromString(element)
                height = int(Example.features.feature['height'].int64_list.value[0])
                width = int(Example.features.feature['width'].int64_list.value[0])
                depth = int(Example.features.feature['depth'].int64_list.value[0])
                img_string = (Example.features.feature['picture_raw'].bytes_list.value[0])
                pict_array.append(np.fromstring(img_string,dtype=np.float32).reshape((height,width,depth)))
                label_array.append( (Example.features.feature['label'].int64_list.value[0]) )
                if i%500 == 0:
                    loop.loop_print(i,time.time())
                pict_array = np.array(pict_array)
                label_array = np.array(label_array)
        print("Shape of the loaded array of pictures:", pict_array.shape)
        print("Shape of the loaded array of labels:", label_array.shape)
        return (pict_array, label_array)


    def split_data(self, x, y, fraction=0.8):
        """
        Splits the data into 'training' and 'testing' datasets according to the specified fraction.          
        
        Arguments:                                                                                           
        1. The actual data values ('x')                                                                      
        2. The label array ('y')                                                                             
        3. The fraction of training data the user wants                                                      
        
        Returns:                                                                                             
        The testing and training data and labels in the following order:                                     
        (x_train, y_train, x_test, y_test)                                                                   
        """
        ###Sanity Check###                                                                                   
        if len(x) != len(y):
            print("ERROR: The arrays of the values and of the labels must have the same size!")
            sys.exit()

        ###Shuffling###                                                                                      
        unison_shuffle(x, y)

        splitting_value = int(len(x)*fraction)
        return x[:splitting_value], y[:splitting_value], x[splitting_value:], y[splitting_value:]