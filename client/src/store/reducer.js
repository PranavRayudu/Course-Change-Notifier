import {
    REQUEST_BROWSER_LOGIN,
    GET_LOGIN,
    SET_CONFIG,
    SET_LOGIN,
    REQUEST_USER_LOGIN,
    GET_COURSES,
    SET_COURSES, ADD_COURSE
} from "./actions";
import moment from "moment";

const initialState = {
    userLogin: false,
    browserLogin: false,
    userLoading: true,
    browserLoading: false,

    sid: '',
    interval: 0,
    timeRange: [null, null],

    courses: [],
    coursesLoading: false,
}

function rootReducer(state = initialState, action) {

    switch (action.type) {
        case GET_LOGIN:
            return {
                ...state,
                userLoading: !state.userLogin
            }
        case SET_LOGIN:
            return {
                ...state,
                userLoading: false,
                browserLoading: false,
                userLogin: action.payload && "user" in action.payload ?
                    action.payload.user : state.userLogin,
                browserLogin: action.payload && "browser" in action.payload ?
                    action.payload.browser : state.browserLogin
            }
        case REQUEST_USER_LOGIN:
            return {
                ...state,
                userLoading: true
            }
        case REQUEST_BROWSER_LOGIN:
            return {
                ...state,
                browserLoading: true
            }
        case SET_CONFIG:
            const data = action.payload
            // let sid = data.sid
            let timeRange = [null, null]

            let interval = parseInt(data.interval)
            if (data.start && data.end)
                timeRange = [moment(data.start, 'HHmm'), moment(data.end, 'HHmm')]
            return {
                ...state,
                // sid: sid,
                interval: interval,
                timeRange: timeRange
            }

        case GET_COURSES:
            return {
                ...state,
                coursesLoading: true
            }
        case SET_COURSES:
            if (action.payload.status === 'fail') {
                return {
                    ...state,
                    coursesLoading: false
                }
            } else {
                let courses = action.payload.courses.map(course => {
                    return {
                        ...course,
                        key: course.uid
                    }
                })

                return {
                    ...state,
                    coursesLoading: false,
                    courses: courses
                }
            }

        case ADD_COURSE:
            let course = {
                ...action.payload,
                key: action.payload.uid
            }

            return {
                ...state,
                coursesLoading: false,
                courses: [...state.courses, course]
            }
        default:
            return state
    }
}

export default rootReducer
